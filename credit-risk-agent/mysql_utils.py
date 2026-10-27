import os
import logging
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

# Fail-fast validation for required environment variables
AWS_MYSQL_USER = os.getenv("AWS_MYSQL_USER")
if not AWS_MYSQL_USER:
    raise RuntimeError("AWS_MYSQL_USER environment variable must be set. Default credentials are not permitted.")

AWS_MYSQL_PASSWORD = os.getenv("AWS_MYSQL_PASSWORD")
if not AWS_MYSQL_PASSWORD:
    raise RuntimeError("AWS_MYSQL_PASSWORD environment variable must be set. Default credentials are not permitted.")

AZURE_MYSQL_USER = os.getenv("AZURE_MYSQL_USER")
if not AZURE_MYSQL_USER:
    raise RuntimeError("AZURE_MYSQL_USER environment variable must be set. Default credentials are not permitted.")

AZURE_MYSQL_PASSWORD = os.getenv("AZURE_MYSQL_PASSWORD")
if not AZURE_MYSQL_PASSWORD:
    raise RuntimeError("AZURE_MYSQL_PASSWORD environment variable must be set. Default credentials are not permitted.")

logger = logging.getLogger(__name__)

def get_fraud_status_aws(customer_id: str) -> dict:
    """
    Connects to AWS RDS MySQL instance to check fraud status.
    """
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(
            host=os.getenv("AWS_MYSQL_HOST", "fraud-db.cluster-xxxx.us-east-1.rds.amazonaws.com"),
            user=AWS_MYSQL_USER,
            password=AWS_MYSQL_PASSWORD,
            database=os.getenv("AWS_MYSQL_DB", "fraud_db"),
            connection_timeout=2
        )
        cursor = connection.cursor(dictionary=True)
        query = "SELECT is_blacklisted, fraud_reason FROM fraud_blacklist WHERE customer_id = %s"
        logger.info(f"Executing AWS MySQL query: {query} with customer_id {customer_id}")
        cursor.execute(query, (customer_id,))
        result = cursor.fetchone()
        return result if result else {"is_blacklisted": "false", "fraud_reason": "No record found"}
    except Exception as e:
        logger.error(f"Error fetching from AWS MySQL: {e}")
        raise e
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def get_fraud_status_azure(customer_id: str) -> dict:
    """
    Connects to Azure Database for MySQL instance to check fraud status.
    """
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(
            host=os.getenv("AZURE_MYSQL_HOST", "fraud-db.mysql.database.azure.com"),
            user=AZURE_MYSQL_USER,
            password=AZURE_MYSQL_PASSWORD,
            database=os.getenv("AZURE_MYSQL_DB", "fraud_db"),
            connection_timeout=2
        )
        cursor = connection.cursor(dictionary=True)
        query = "SELECT is_blacklisted, fraud_reason FROM finance_agent_schema.test_cust_blacklist_status WHERE customer_id = %s"
        logger.info(f"Executing Azure MySQL query: {query} with customer_id {customer_id}")
        cursor.execute(query, (customer_id,))
        result = cursor.fetchone()
        return result if result else {"is_blacklisted": "false", "fraud_reason": "No record found"}
    except Exception as e:
        logger.error(f"Error fetching from Azure MySQL: {e}")
        raise e
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
