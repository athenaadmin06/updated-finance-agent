# Decoy: correct pattern, nothing hardcoded
import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

vault_url = os.environ["KEY_VAULT_URL"]
client = SecretClient(vault_url=vault_url, credential=DefaultAzureCredential())
db_password = client.get_secret("db-password").value
api_key = os.getenv("AZURE_OPENAI_API_KEY")
password = "changeme"
client_secret = "<your-client-secret>"
token = "${SAS_TOKEN}"
