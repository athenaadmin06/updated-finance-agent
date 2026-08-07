import os
from dotenv import load_dotenv

load_dotenv()

from logic import assess_credit_risk

def test():
    print("Starting agent tests...")
    
    for customer_id in ["C005", "C006"]:
        print(f"\n--- Testing {customer_id} ---")
        profile_text = f"Applicant Name: Test User {customer_id}. Age: 30. Requested Loan: 290,000."
        
        # We pass uploaded_files=None to skip S3 and OpenSearch ingestion for this quick test.
        result = assess_credit_risk(customer_id, profile_text, uploaded_files=None)
        
        print(f"\n\n=== FINAL AGENT DECISION FOR {customer_id} ===")
        print(result)

if __name__ == "__main__":
    test()
