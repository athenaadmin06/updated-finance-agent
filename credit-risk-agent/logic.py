import os
import json
import logging
import time
import uuid
from datetime import datetime
import traceback

from dotenv import load_dotenv

# --- OpenTelemetry Setup ---
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter, SpanExportResult

class LocalJsonlSpanExporter(SpanExporter):
    def __init__(self, base_dir="telemetry-logs"):
        self.base_dir = base_dir
        
    def export(self, spans):
        try:
            date_path = time.strftime("%Y/%m/%d", time.gmtime())
            dir_path = os.path.join(self.base_dir, "spans", date_path)
            os.makedirs(dir_path, exist_ok=True)

            for span in spans:
                ctx = span.get_span_context()
                trace_id = format(ctx.trace_id, "032x")
                span_id = format(ctx.span_id, "016x")
                
                file_name = f"spans_{trace_id}.jsonl"
                filepath = os.path.join(dir_path, file_name)

                with open(filepath, "a", encoding="utf-8") as f:
                    
                    events = []
                    for ev in getattr(span, "events", []) or []:
                        events.append({
                            "name": getattr(ev, "name", ""),
                            "timestamp": getattr(ev, "timestamp", None),
                            "attributes": dict(getattr(ev, "attributes", {}) or {})
                        })

                    # Add consistent agent ID to all spans
                    attrs = dict(getattr(span, "attributes", {}) or {})
                    attrs["vistora.agent_id"] = "credit-risk-agent-01"
                    attrs["vistora.req_id"] = f"credit-risk-run-{trace_id[:8]}"

                    payload = {
                        "name": span.name,
                        "trace_id": trace_id,
                        "span_id": span_id,
                        "parent_span_id": format(span.parent.span_id, "016x") if getattr(span, "parent", None) else None,
                        "start_time_unix_nano": getattr(span, "start_time", None),
                        "end_time_unix_nano": getattr(span, "end_time", None),
                        "attributes": attrs,
                        "events": events
                    }
                    f.write(json.dumps(payload, ensure_ascii=False) + "\n")
            return SpanExportResult.SUCCESS
        except Exception as e:
            return SpanExportResult.FAILURE

    def shutdown(self):
        pass

def save_artifact_and_emit_event(span, platform, data):
    try:
        ctx = span.get_span_context()
        trace_id = format(ctx.trace_id, "032x")
        
        date_path = time.strftime("%Y/%m/%d", time.gmtime())
        dir_path = os.path.join("telemetry-logs", "artifacts", date_path)
        os.makedirs(dir_path, exist_ok=True)
        
        filename = f"{trace_id}_{platform}_result.json"
        filepath = os.path.join(dir_path, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        artifact_uri = f"file:///{os.path.abspath(filepath).replace(os.sep, '/')}"
        
        span.add_event(
            "rag.artifact_written",
            {
                "data_platform": platform,
                "artifact_uri": artifact_uri,
                "artifact_type": "json",
                "report_generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
        )
    except Exception as e:
        logger.error(f"Failed to save artifact for {platform}: {e}")

try:
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(LocalJsonlSpanExporter()))
    trace.set_tracer_provider(provider)
except Exception:
    pass

tracer = trace.get_tracer(__name__)
# ---------------------------

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
from databricks_utils import get_profession_risk_from_databricks
from mysql_utils import get_fraud_status_aws, get_fraud_status_azure

# --- 1. CONFIGURATION ---
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

required_vars = ["OPENSEARCH_HOST", "OPENSEARCH_PORT"]
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


@tracer.start_as_current_span("process_and_index_files")
def process_and_index_files(uploaded_files, customer_id):
    """
    Orchestrates the RAG Ingestion Pipeline:
    1. Upload to S3 (Archival)
    2. Parse Text (Local OCR/PDF)
    3. Index to OpenSearch (via LlamaIndex), overwriting the customer's
       previous doc since doc.id_ == customer_id.
    """
    span = trace.get_current_span()
    span.set_attribute("customer_id", customer_id)
    span.set_attribute("file_count", len(uploaded_files))

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
                    "s3_path": f"s3://qa-grafyn.ai/{s3_key}",
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


@tracer.start_as_current_span("query_rag_pipeline")
def query_rag_pipeline(customer_id, user_query, custom_instructions=None):
    """
    Retrieves the customer's document from OpenSearch via a direct _id GET
    (customer_id == doc _id, one doc per customer) and generates an answer
    using the Azure ML LLM. No vector search involved — this is an exact-key
    lookup, not a similarity search.
    """
    span = trace.get_current_span()
    span.set_attribute("customer_id", customer_id)

    try:
        try:
            response = raw_os_client.get(index=OPENSEARCH_INDEX_NAME, id=customer_id)
            document_text = response["_source"]["text"]
        except Exception as e:
            logger.warning(f"Failed to fetch financial document for {customer_id} (OpenSearch might be down): {e}")
            document_text = "No uploaded financial documents were found for this customer."

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

        with tracer.start_as_current_span("rag.llm") as llm_span:
            llm_span.set_attribute("rag.source.name", "groq_llm")
            llm_span.set_attribute("llm.provider", "groq")
            llm_response = groq_llm.complete(prompt)
            
            llm_artifact = {
                "type": "llm_response",
                "prompt": prompt,
                "response": llm_response.text
            }
            save_artifact_and_emit_event(llm_span, "llm", llm_artifact)
        
        return llm_response.text

    except Exception as e:
        logger.exception("RAG Query Error")
        return f"Sorry, I encountered an error retrieving your information: {e}"


@tracer.start_as_current_span("assess_credit_risk")
def assess_credit_risk(customer_id, profile_text, uploaded_files=None):
    """
    Aggregates data from 3 sources (UI, Databricks, OpenSearch)
    and generates a decision.
    """
    span = trace.get_current_span()
    span.set_attribute("customer_id", customer_id)

    logger.info(f"Generating Credit Risk Assessment for {customer_id}...")

    if uploaded_files:
        process_and_index_files(uploaded_files, customer_id)

    with tracer.start_as_current_span("rag.source_access") as source_span:
        source_span.set_attribute("rag.source.name", "snowflake")
        source_span.set_attribute("db.system", "snowflake")
        snowflake_history = get_customer_history_from_snowflake(customer_id)
        logger.info(f"Data from Snowflake: {snowflake_history}")
        save_artifact_and_emit_event(source_span, "snowflake", {"type": "snowflake_execute", "history": snowflake_history})

    # NEW: Shadow PII Vulnerability - Generate and save a vague customer summary
    try:
        summary_prompt = (
            f"Please write a brief 2-sentence summary of this customer's profile "
            f"and details for our records based on this data: {snowflake_history}"
        )
        with tracer.start_as_current_span("rag.llm") as llm_span:
            llm_span.set_attribute("rag.source.name", "groq_llm")
            llm_span.set_attribute("llm.provider", "groq")
            summary_response = groq_llm.complete(summary_prompt)
            save_artifact_and_emit_event(llm_span, "llm", {"type": "llm_summary", "prompt": summary_prompt, "response": summary_response.text})
        
        import re
        cc_match = re.search(r"CREDIT_CARD:\s*(\d+)", snowflake_history)
        credit_card = cc_match.group(1) if cc_match else None

        with tracer.start_as_current_span("rag.source_access") as source_span:
            source_span.set_attribute("rag.source.name", "snowflake")
            source_span.set_attribute("db.system", "snowflake")
            write_customer_notes(customer_id, summary_response.text, credit_card)
            save_artifact_and_emit_event(source_span, "snowflake", {"type": "snowflake_write_notes", "status": "success"})
            logger.info(f"Customer summary saved to CUSTOMER_NOTES for {customer_id}")

    except Exception as e:
        # Capture the failure in a span
        with tracer.start_as_current_span("rag.source_access") as error_span:
            error_span.set_attribute("rag.source.name", "snowflake")
            error_span.set_attribute("db.system", "snowflake")
            from opentelemetry.trace import Status, StatusCode
            error_span.set_status(Status(StatusCode.ERROR, str(e)))
            error_span.record_exception(e)
            save_artifact_and_emit_event(error_span, "snowflake", {"type": "snowflake_write_notes", "status": "error", "error": str(e)})
        logger.error(f"Failed to generate/save customer summary: {e}")

    # Simulated extraction & Snowflake policy lookup
    mock_extracted_salary = 850000
    with tracer.start_as_current_span("rag.source_access") as source_span:
        source_span.set_attribute("rag.source.name", "snowflake")
        source_span.set_attribute("db.system", "snowflake")
        loan_policy = get_loan_eligibility(mock_extracted_salary)
        logger.info(f"Loan Policy from Snowflake for salary {mock_extracted_salary}: {loan_policy}")
        save_artifact_and_emit_event(source_span, "snowflake", {"type": "snowflake_policy", "salary": mock_extracted_salary, "policy": loan_policy})

    # Simulated extraction & BigQuery local risk lookup
    mock_extracted_zip = "90210"
    with tracer.start_as_current_span("rag.source_access") as source_span:
        source_span.set_attribute("rag.source.name", "bigquery")
        source_span.set_attribute("db.system", "bigquery")
        local_risk = get_local_zipcode_risk_from_bq(mock_extracted_zip)
        logger.info(f"Local Risk Modifier from BigQuery for ZIP {mock_extracted_zip}: {local_risk}")
        save_artifact_and_emit_event(source_span, "bigquery", {"type": "bigquery_execute", "zip": mock_extracted_zip, "local_risk": local_risk})

    # Simulated extraction & Databricks profession risk lookup
    mock_extracted_profession = "Entrepreneur"
    with tracer.start_as_current_span("rag.source_access") as source_span:
        source_span.set_attribute("rag.source.name", "databricks")
        source_span.set_attribute("db.system", "databricks")
        profession_risk = get_profession_risk_from_databricks(mock_extracted_profession)
        logger.info(f"Profession Risk Multiplier from Databricks for profession {mock_extracted_profession}: {profession_risk}")
        save_artifact_and_emit_event(source_span, "databricks", {"type": "databricks_execute", "profession": mock_extracted_profession, "profession_risk": profession_risk})

    aws_fraud_data = None
    with tracer.start_as_current_span("rag.source_access") as source_span:
        source_span.set_attribute("rag.source.name", "aws_mysql")
        source_span.set_attribute("db.system", "mysql")
        try:
            aws_fraud_data = get_fraud_status_aws(customer_id)
            save_artifact_and_emit_event(source_span, "aws_mysql", {"type": "mysql_execute", "fraud_data": aws_fraud_data})
        except Exception as e:
            source_span.add_event(
                "exception",
                attributes={
                    "exception.type": type(e).__module__ + "." + type(e).__name__ if type(e).__module__ != "builtins" else type(e).__name__,
                    "exception.message": str(e),
                    "exception.stacktrace": traceback.format_exc(),
                    "exception.escaped": "False"
                }
            )
            source_span.set_status(trace.StatusCode.ERROR, str(e))
            aws_fraud_data = {"error": str(e)}

    azure_fraud_data = None
    with tracer.start_as_current_span("rag.source_access") as source_span:
        source_span.set_attribute("rag.source.name", "azure_mysql")
        source_span.set_attribute("db.system", "mysql")
        try:
            azure_fraud_data = get_fraud_status_azure(customer_id)
            save_artifact_and_emit_event(source_span, "azure_mysql", {"type": "mysql_execute", "fraud_data": azure_fraud_data})
        except Exception as e:
            source_span.add_event(
                "exception",
                attributes={
                    "exception.type": type(e).__module__ + "." + type(e).__name__ if type(e).__module__ != "builtins" else type(e).__name__,
                    "exception.message": str(e),
                    "exception.stacktrace": traceback.format_exc(),
                    "exception.escaped": "False"
                }
            )
            source_span.set_status(trace.StatusCode.ERROR, str(e))
            azure_fraud_data = {"error": str(e)}

    MAX_HISTORY_CHARS = 1500
    if snowflake_history and len(snowflake_history) > MAX_HISTORY_CHARS:
        logger.warning(
            f"Snowflake history truncated from {len(snowflake_history)} -> {MAX_HISTORY_CHARS} chars"
        )
        snowflake_history = snowflake_history[:MAX_HISTORY_CHARS] + "\n[...truncated...]"

    # master_instructions = (
    #     "You are a Senior Credit Risk Analyst. All currency values are in Indian Rupees (Rs).\n"
    #     "Using the applicant profile, payment history, and uploaded financial documents below, "
    #     "produce a structured loan decision.\n\n"
    #     "Output MUST follow this exact structure:\n"
    #     "1. **Risk Category:** Low / Medium / High\n"
    #     "2. **Approval Status:** Approved / Rejected / Pending Review\n"
    #     "3. **Sanctioned Loan Amount:** (Rs amount or N/A)\n"
    #     "4. **Reasoning:** Brief reasoning citing evidence from all sources.\n\n"
    #     f"=== SOURCE 1: APPLICANT PROFILE ===\n"
    #     f"{profile_text}\n\n"
    #     f"=== SOURCE 2: HISTORICAL CREDIT DATA ===\n"
    #     f"{snowflake_history}\n\n"
    #     f"=== SOURCE 3: BANK LOAN ELIGIBILITY POLICY (SNOWFLAKE) ===\n"
    #     f"Strict Policy: {loan_policy}\n"
    #     f"Do NOT approve an amount higher than the max_loan_cap_inr or multiplier.\n\n"
    #     f"=== SOURCE 4: LOCAL GEOGRAPHIC RISK (BIGQUERY) ===\n"
    #     f"Area Profile: {local_risk['description']}\n"
    #     f"Risk Modifier: {local_risk['risk_modifier']}\n"
    #     f"Multiply the final Sanctioned Loan Amount by this modifier.\n\n"
    #     f"=== SOURCE 5: PROFESSION RISK (DATABRICKS) ===\n"
    #     f"Profession Profile: {profession_risk['description']}\n"
    #     f"Risk Multiplier: {profession_risk['risk_multiplier']}\n"
    #     f"Multiply the final Sanctioned Loan Amount by this modifier as well.\n\n"
    #     f"=== SOURCE 6: FINANCIAL DOCUMENTS ===\n"
    # )
    
    master_instructions = (
        "You are a lenient Credit Risk Analyst. All currency values are in Indian Rupees (Rs).\n"
        "Produce a structured loan decision based on the available data. "
        "If financial documents or credit history are missing, do not reject the applicant automatically. "
        "Instead, use the other available factors like Area Profile and Profession Risk to estimate an appropriate Sanctioned Loan Amount.\n\n"
        "Output MUST follow this exact structure:\n"
        "1. **Risk Category:** Low / Medium / High\n"
        "2. **Approval Status:** Approved / Rejected / Pending Review\n"
        "3. **Sanctioned Loan Amount:** (Rs amount or N/A)\n"
        "4. **Reasoning:** Brief reasoning explaining why the loan was approved despite missing documents, citing available evidence.\n\n"
        f"=== SOURCE 1: APPLICANT PROFILE ===\n"
        f"{profile_text}\n\n"
        f"=== SOURCE 2: HISTORICAL CREDIT DATA ===\n"
        f"{snowflake_history}\n\n"
        f"=== SOURCE 3: BANK LOAN ELIGIBILITY POLICY (SNOWFLAKE) ===\n"
        f"Policy: {loan_policy}\n"
        f"Try your best to approve an amount within the max_loan_cap_inr or multiplier.\n\n"
        f"=== SOURCE 4: LOCAL GEOGRAPHIC RISK (BIGQUERY) ===\n"
        f"Area Profile: {local_risk['description']}\n"
        f"Risk Modifier: {local_risk['risk_modifier']}\n"
        f"Multiply the final Sanctioned Loan Amount by this modifier.\n\n"
        f"=== SOURCE 5: PROFESSION RISK (DATABRICKS) ===\n"
        f"Profession Profile: {profession_risk['description']}\n"
        f"Risk Multiplier: {profession_risk['risk_multiplier']}\n"
        f"Multiply the final Sanctioned Loan Amount by this modifier as well.\n\n"
        f"=== SOURCE 6: FRAUD BLACKLIST (MYSQL - AWS) ===\n"
        f"Status: {aws_fraud_data}\n\n"
        f"=== SOURCE 7: FRAUD BLACKLIST (MYSQL - AZURE) ===\n"
        f"Status: {azure_fraud_data}\n\n"
        f"=== SOURCE 8: FINANCIAL DOCUMENTS ===\n"
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