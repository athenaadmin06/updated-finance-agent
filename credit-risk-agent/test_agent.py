import os
from dotenv import load_dotenv

load_dotenv()

from logic import assess_credit_risk

def test():
    print("Starting agent test...")
    customer_id = "C004"
    profile_text = "Applicant Name: Priya Kapoor. Age: 30. Requested Loan: 290,000."
    
    # We pass uploaded_files=None to skip S3 and OpenSearch ingestion for this quick test.
    result = assess_credit_risk(customer_id, profile_text, uploaded_files=None)
    
    print("\n\n=== FINAL AGENT DECISION ===")
    print(result)

if __name__ == "__main__":
    test()
