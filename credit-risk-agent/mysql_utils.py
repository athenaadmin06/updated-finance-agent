import os
import logging
import mysql.connector
from dotenv import load_dotenv

load_dotenv()
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
            user=os.getenv("AWS_MYSQL_USER", "admin"),
            password=os.getenv("AWS_MYSQL_PASSWORD", "dummy_pass"),
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
            user=os.getenv("AZURE_MYSQL_USER", "admin"),
            password=os.getenv("AZURE_MYSQL_PASSWORD", "dummy_pass"),
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
