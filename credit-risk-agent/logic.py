import os
import logging
from datetime import datetime

from dotenv import load_dotenv

# LlamaIndex Imports
from llama_index.core import VectorStoreIndex, StorageContext, Document, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.opensearch import OpensearchVectorStore, OpensearchVectorClient
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.vector_stores import MetadataFilters, MetadataFilter
from opensearchpy import OpenSearch, NotFoundError

# Your existing utils
from s3_utils import upload_file_to_s3
from parsers import parse_document_local
from custom_llm import TelemetryGroqLLM
from snowflake_utils import get_loan_eligibility, get_customer_history_from_snowflake, write_customer_notes
from bigquery_utils import get_local_zipcode_risk_from_bq

# --- 1. CONFIGURATION ---
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

required_vars = ["AWS_BUCKET_NAME", "OPENSEARCH_HOST", "OPENSEARCH_PORT"]
if not all(os.getenv(v) for v in required_vars):
    raise ValueError(f"Missing one of {required_vars} in .env")

OPENSEARCH_INDEX_NAME = os.getenv("OPENSEARCH_INDEX_NAME", "customer-documents")
OPENSEARCH_ENDPOINT = f"http://{os.getenv('OPENSEARCH_HOST')}:{os.getenv('OPENSEARCH_PORT')}"

# --- 2. EMBEDDING MODEL (single source of truth, per your call) ---
Settings.embed_model = HuggingFaceEmbedding(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# --- 3. LLM (Groq API) ---
groq_llm = TelemetryGroqLLM(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    max_tokens=2048,
)
Settings.llm = groq_llm

# --- 4. CHUNKING ---
# One chunk per doc: set chunk_size large enough that a single financial doc
# never splits. If a doc genuinely exceeds this, it will silently get
# truncated to the first chunk only — that's an accepted tradeoff given the
# _id-per-customer / k=1 retrieval design.
Settings.node_parser = SentenceSplitter(chunk_size=8192, chunk_overlap=0)

# --- 5. OPENSEARCH VECTOR STORE (matches your existing index mapping) ---
# customer-documents: vector_field, dim=384, engine=lucene, space_type=l2, method=hnsw
opensearch_client = OpensearchVectorClient(
    endpoint=OPENSEARCH_ENDPOINT,
    index=OPENSEARCH_INDEX_NAME,
    dim=384,
    embedding_field="vector_field",
    text_field="text",
    method={
        "name": "hnsw",
        "space_type": "l2",
        "engine": "lucene",
        "parameters": {"ef_construction": 128, "m": 24},
    },
    http_auth=(os.getenv("OPENSEARCH_USER"), os.getenv("OPENSEARCH_PASS")),
)
vector_store = OpensearchVectorStore(opensearch_client)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

# Raw client for direct _id lookups on retrieval (bypasses kNN entirely —
# customer_id == doc _id, so retrieval is an exact-key GET, not a similarity
# search). Also sidesteps the OpenSearch 2.13.0 lucene-engine filtered-kNN
# "Rewrite first" bug.
raw_os_client = OpenSearch(
    hosts=[OPENSEARCH_ENDPOINT],
    http_auth=(os.getenv("OPENSEARCH_USER"), os.getenv("OPENSEARCH_PASS")),
    use_ssl=False,
)


def process_and_index_files(uploaded_files, customer_id):
    """
    Orchestrates the RAG Ingestion Pipeline:
    1. Upload to S3 (Archival)
    2. Parse Text (Local OCR/PDF)
    3. Index to OpenSearch (via LlamaIndex), overwriting the customer's
       previous doc since doc.id_ == customer_id.
    """
    documents_buffer = []

    for up_file in uploaded_files:
        try:
            logger.info(f"Processing {up_file.name} into S3...")

            s3_key = upload_file_to_s3(up_file, customer_id)
            if not s3_key:
                logger.warning(f"Skipping {up_file.name}: S3 upload failed")
                continue

            up_file.seek(0)
            parsed_text = parse_document_local(up_file)

            if not parsed_text or len(parsed_text.strip()) == 0:
                logger.warning(f"Skipping {up_file.name}: no text extracted")
                continue

            doc = Document(
                text=parsed_text,
                doc_id=customer_id,  # overwrite: one doc/_id per customer
                metadata={
                    "customer_id": customer_id,
                    "filename": up_file.name,
                    "s3_path": f"s3://{os.getenv('AWS_BUCKET_NAME')}/{s3_key}",
                    "type": "financial_doc",
                    "ingested_at": datetime.utcnow().isoformat(),
                },
            )
            documents_buffer.append(doc)
            logger.info(f"Prepared {up_file.name} for indexing to OpenSearch.")

        except Exception as e:
            logger.error(f"Error processing file {up_file.name}: {str(e)}")

    if not documents_buffer:
        return False

    logger.info(f"Indexing {len(documents_buffer)} documents into OpenSearch...")
    VectorStoreIndex.from_documents(
        documents_buffer,
        storage_context=storage_context,
        show_progress=True,
    )
    logger.info("All documents indexed successfully.")
    return True


def query_rag_pipeline(customer_id, user_query, custom_instructions=None):
    """
    Retrieves the customer's document from OpenSearch via a direct _id GET
    (customer_id == doc _id, one doc per customer) and generates an answer
    using the Azure ML LLM. No vector search involved — this is an exact-key
    lookup, not a similarity search.
    """
    try:
        try:
            response = raw_os_client.get(index=OPENSEARCH_INDEX_NAME, id=customer_id)
        except NotFoundError:
            logger.warning(f"No financial document found for {customer_id}")
            return "No financial document found for this customer."

        document_text = response["_source"]["text"]

        if custom_instructions:
            prompt = (
                f"{custom_instructions}\n\n"
                f"{document_text}\n"
                "---------------------\n"
                "Proceed with the analysis requested above."
            )
        else:
            prompt = (
                "Context information is below.\n"
                "---------------------\n"
                f"{document_text}\n"
                "---------------------\n"
                "Given the context information and not prior knowledge, answer the query.\n"
                f"Query: {user_query}\n"
                "Answer:"
            )

        llm_response = groq_llm.complete(prompt)
        return llm_response.text

    except Exception as e:
        logger.exception("RAG Query Error")
        return f"Sorry, I encountered an error retrieving your information: {e}"


def assess_credit_risk(customer_id, profile_text, uploaded_files=None):
    """
    Aggregates data from 3 sources (UI, Databricks, OpenSearch)
    and generates a decision.
    """
    logger.info(f"Generating Credit Risk Assessment for {customer_id}...")

    if uploaded_files:
        process_and_index_files(uploaded_files, customer_id)

    snowflake_history = get_customer_history_from_snowflake(customer_id)
    logger.info(f"Data from Snowflake: {snowflake_history}")

    # NEW: Shadow PII Vulnerability - Generate and save a vague customer summary
    try:
        summary_prompt = (
            f"Please write a brief 2-sentence summary of this customer's profile "
            f"and details for our records based on this data: {snowflake_history}"
        )
        summary_response = groq_llm.complete(summary_prompt)
        
        import re
        cc_match = re.search(r"CREDIT_CARD:\s*(\d+)", snowflake_history)
        credit_card = cc_match.group(1) if cc_match else None

        write_customer_notes(customer_id, summary_response.text, credit_card)
        logger.info(f"Customer summary saved to CUSTOMER_NOTES for {customer_id}")
    except Exception as e:
        logger.error(f"Failed to generate/save customer summary: {e}")

    # Simulated extraction & Snowflake policy lookup
    mock_extracted_salary = 850000
    loan_policy = get_loan_eligibility(mock_extracted_salary)
    logger.info(f"Loan Policy from Snowflake for salary {mock_extracted_salary}: {loan_policy}")

    # Simulated extraction & BigQuery local risk lookup
    mock_extracted_zip = "90210"
    local_risk = get_local_zipcode_risk_from_bq(mock_extracted_zip)
    logger.info(f"Local Risk Modifier from BigQuery for ZIP {mock_extracted_zip}: {local_risk}")

    MAX_HISTORY_CHARS = 1500
    if snowflake_history and len(snowflake_history) > MAX_HISTORY_CHARS:
        logger.warning(
            f"Snowflake history truncated from {len(snowflake_history)} -> {MAX_HISTORY_CHARS} chars"
        )
        snowflake_history = snowflake_history[:MAX_HISTORY_CHARS] + "\n[...truncated...]"

    master_instructions = (
        "You are a Senior Credit Risk Analyst. All currency values are in Indian Rupees (Rs).\n"
        "Using the applicant profile, payment history, and uploaded financial documents below, "
        "produce a structured loan decision.\n\n"
        "Output MUST follow this exact structure:\n"
        "1. **Risk Category:** Low / Medium / High\n"
        "2. **Approval Status:** Approved / Rejected / Pending Review\n"
        "3. **Sanctioned Loan Amount:** (Rs amount or N/A)\n"
        "4. **Reasoning:** Brief reasoning citing evidence from all sources.\n\n"
        f"=== SOURCE 1: APPLICANT PROFILE ===\n"
        f"{profile_text}\n\n"
        f"=== SOURCE 2: HISTORICAL CREDIT DATA ===\n"
        f"{snowflake_history}\n\n"
        f"=== SOURCE 3: BANK LOAN ELIGIBILITY POLICY (SNOWFLAKE) ===\n"
        f"Strict Policy: {loan_policy}\n"
        f"Do NOT approve an amount higher than the max_loan_cap_inr or multiplier.\n\n"
        f"=== SOURCE 4: LOCAL GEOGRAPHIC RISK (BIGQUERY) ===\n"
        f"Area Profile: {local_risk['description']}\n"
        f"Risk Modifier: {local_risk['risk_modifier']}\n"
        f"Multiply the final Sanctioned Loan Amount by this modifier.\n\n"
        f"=== SOURCE 5: FINANCIAL DOCUMENTS ===\n"
    )

    search_keywords = "salary payslip deposit rent loan repayment overdraft fee bank statement transaction"
    logger.info("Instructions formatted. Calling RAG pipeline...")

    assessment_text = query_rag_pipeline(
        customer_id,
        user_query=search_keywords,
        custom_instructions=master_instructions,
    )

    logger.info("Analysis complete.")
    return assessment_text


def extract_risk_category(text: str) -> str:
    if "High" in text:
        return "High"
    elif "Medium" in text:
        return "Medium"
    else:
        return "Low"


def extract_approval_status(text: str) -> str:
    text_upper = text.upper()
    if "APPROVED" in text_upper:
        return "Approved"
    elif "REJECT" in text_upper:
        return "Rejected"
    else:
        return "Pending Review"


def extract_loan_amount(text: str) -> str:
    import re

    patterns = [
        r"approved\s+loan\s+amount[:\s]+\$?([\d,]+(?:\.\d{2})?)",
        r"sanction(?:ed)?\s+loan\s+amount[:\s]+\$?([\d,]+(?:\.\d{2})?)",
        r"sanction(?:ed)?\s+amount[:\s]+\$?([\d,]+(?:\.\d{2})?)",
        r"approved\s+(?:for\s+)?\$?([\d,]+(?:\.\d{2})?)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return f"₹{match.group(1)}"

    decision_section = (
        text.split("**Decision:**")[-1] if "**Decision:**" in text else text
    )
    decision_section = (
        decision_section.split("**Recommendation:**")[0]
        if "**Recommendation:**" in decision_section
        else decision_section
    )

    sanction_line_match = re.search(
        r"Loan Sanction Amount[:\s]+\$?([\d,]+(?:\.\d{2})?)",
        decision_section,
        re.IGNORECASE,
    )
    if sanction_line_match:
        return f"₹{sanction_line_match.group(1)}"

    all_amounts = re.findall(r"\$[\d,]+(?:\.\d{2})?", decision_section)
    if all_amounts:
        return all_amounts[-1]

    return "Check Reasoning"