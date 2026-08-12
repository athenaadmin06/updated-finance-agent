import os
import logging
import redshift_connector
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

def get_fraud_status_redshift(customer_id: str) -> dict:
    """
    Connects to AWS Redshift instance to check fraud status.
    """
    connection = None
    cursor = None
    try:
        connection = redshift_connector.connect(
            host=os.getenv("REDSHIFT_HOST", "dummy-redshift.amazonaws.com"),
            port=int(os.getenv("REDSHIFT_PORT", 5439)),
            user=os.getenv("REDSHIFT_USER", "admin"),
            password=os.getenv("REDSHIFT_PASSWORD", "dummy"),
            database=os.getenv("REDSHIFT_DB", "finance_agent_schema")
        )
        cursor = connection.cursor()
        query = "SELECT is_blacklisted, fraud_reason FROM finance_agent_schema.test_cust_blacklist_status WHERE customer_id = %s"
        logger.info(f"Executing Redshift query: {query} with customer_id {customer_id}")
        cursor.execute(query, (customer_id,))
        result = cursor.fetchone()
        
        if result:
            return {"is_blacklisted": str(result[0]).lower(), "fraud_reason": str(result[1])}
        return {"is_blacklisted": "false", "fraud_reason": "No record found"}
    except Exception as e:
        logger.error(f"Error fetching from Redshift: {e}")
        raise e
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
