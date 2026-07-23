import os
try:
    from google.cloud import bigquery
except ImportError:
    bigquery = None

def get_local_zipcode_risk_from_bq(zip_code):
    """
    Queries the 'vistora_db.local_risk_data' table in BigQuery 
    to get geographic risk modifiers for the applicant's ZIP code.
    """
    # 1. Check if we have credentials set up for real execution
    if bigquery and os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        try:
            client = bigquery.Client()
            query = f"""
                SELECT 
                    zip_code,
                    area_median_income,
                    risk_modifier,
                    description
                FROM 
                    `vistora_db.local_risk_data`
                WHERE 
                    zip_code = {zip_code}
            """
            
            print(f"Executing BigQuery: {query}")
            query_job = client.query(query)
            results = query_job.result()
            
            for row in results:
                return {
                    "risk_modifier": row.risk_modifier,
                    "description": row.description
                }
                
            return {"risk_modifier": 1.0, "description": "Unknown area, standard risk"}

        except Exception as e:
            print(f"BigQuery Execution Error: {e}")
            # Fall through to mock data if it fails
    
    # 2. Mock Data Fallback (for testing without GCP credentials)
    print(f"Executing mock BigQuery fetch for {zip_code} on vistora_db.local_risk_data...")
    if str(zip_code) == "90210":
        return {"risk_modifier": 0.8, "description": "Low risk area, increase loan cap by 20%"}
    elif str(zip_code) == "33101":
        return {"risk_modifier": 1.2, "description": "High risk area, decrease loan cap by 20%"}
    else:
        return {"risk_modifier": 1.0, "description": "Standard risk area, no change"}
