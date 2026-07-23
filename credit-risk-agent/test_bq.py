import os
from dotenv import load_dotenv

load_dotenv()
from bigquery_utils import get_local_zipcode_risk_from_bq

print("Testing BigQuery Integration with zipcode '90210'...")
result = get_local_zipcode_risk_from_bq("90210")

print("\n--- BigQuery Result ---")
print(result)
