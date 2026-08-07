import os
import snowflake.connector
from dotenv import load_dotenv

load_dotenv()

def get_loan_eligibility(salary_inr):
    """
    Fetches loan eligibility policy (multiplier and cap) from the Snowflake 
    'salary_loan' table based on the extracted salary.
    Note: This is a placeholder/mock implementation of the Snowflake query.
    """
    try:
        # Example of what the real implementation might look like:
        # import snowflake.connector
        # conn = snowflake.connector.connect(...)
        # cursor = conn.cursor()
        
        query = """
            SELECT max_loan_multiplier, max_loan_cap_inr 
            FROM salary_loan 
            WHERE %s BETWEEN min_salary_inr AND max_salary_inr
        """
        print(f"Executing Snowflake query: {query} with salary {salary_inr}")
        
        # cursor.execute(query, (salary_inr,))
        # result = cursor.fetchone()
        
        # Mocking the Snowflake database response based on the salary
        if salary_inr <= 300000:
            return {"max_loan_multiplier": 0.0, "max_loan_cap_inr": 0}
        elif salary_inr <= 800000:
            return {"max_loan_multiplier": 3.0, "max_loan_cap_inr": 1500000}
        elif salary_inr <= 2000000:
            return {"max_loan_multiplier": 5.0, "max_loan_cap_inr": 5000000}
        else:
            return {"max_loan_multiplier": 7.0, "max_loan_cap_inr": 15000000}

    except Exception as e:
        print(f"Error fetching eligibility from Snowflake: {e}")
        return None

def get_customer_history_from_snowflake(customer_id):
    """
    Fetches structured payment history from Snowflake,
    including column names for better context.
    """
    try:
        connection = snowflake.connector.connect(
            user=os.getenv("SNOWFLAKE_USER"),
            password=os.getenv("SNOWFLAKE_TOKEN"),
            account=os.getenv("SNOWFLAKE_ACCOUNT"),
            warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
            database=os.getenv("SNOWFLAKE_DATABASE", "VISTORA_DB"),
            schema=os.getenv("SNOWFLAKE_SCHEMA", "VISTORA_SCHEMA"),
            role=os.getenv("SNOWFLAKE_ROLE")
        )

        cursor = connection.cursor()

        # Define table path (Modify these as needed)
        database = "VISTORA_DB" 
        schema = "VISTORA_SCHEMA"
        table = "CUSTOMER_PAYMENT_HISTORY"
        full_table_path = f"{database}.{schema}.{table}"
        
        # Execute Query
        query = f"SELECT * FROM {full_table_path} WHERE customer_id = %s"
        cursor.execute(query, (customer_id,))
        
        # 1. Fetch Data
        row = cursor.fetchone()
        
        if row:
            # 2. Fetch Column Names from cursor.description
            col_names = [desc[0] for desc in cursor.description]
            
            # 3. Combine Names with Values
            history_dict = dict(zip(col_names, row))
            
            # 4. Format nicely for the LLM
            formatted_history = ", ".join(
                [f"{k}: {v}" for k, v in history_dict.items() if k.lower() != 'customer_id']
            )
            
            return f"Customer History: [{formatted_history}]"
        else:
            return "No prior customer history found in Snowflake."

    except Exception as e:
        print(f"Snowflake SQL Error: {e}")
        return "Error fetching history."
    
    finally:
        if 'cursor' in locals() and cursor: cursor.close()
        if 'connection' in locals() and connection: connection.close()

def write_customer_notes(customer_id, notes_text, credit_card):
    """
    Writes a customer summary/notes into the CUSTOMER_NOTES table, explicitly including the credit card.
    """
    try:
        connection = snowflake.connector.connect(
            user=os.getenv("SNOWFLAKE_USER"),
            password=os.getenv("SNOWFLAKE_TOKEN"),
            account=os.getenv("SNOWFLAKE_ACCOUNT"),
            warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
            database=os.getenv("SNOWFLAKE_DATABASE", "VISTORA_DB"),
            schema=os.getenv("SNOWFLAKE_SCHEMA", "VISTORA_SCHEMA"),
            role=os.getenv("SNOWFLAKE_ROLE")
        )

        cursor = connection.cursor()

        # Execute Query
        query = "INSERT INTO vistora_db.vistora_schema.CUSTOMER_NOTES (customer_id, notes, credit_card) VALUES (%s, %s, %s)"
        cursor.execute(query, (customer_id, notes_text, credit_card))
        
        # Commit if needed
        connection.commit()
        print(f"Successfully saved notes for {customer_id}")

    except Exception as e:
        print(f"Error writing customer notes to Snowflake: {e}")
        raise e
    
    finally:
        if 'cursor' in locals() and cursor: cursor.close()
        if 'connection' in locals() and connection: connection.close()
