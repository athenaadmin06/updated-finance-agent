# FAKE credentials for scanner testing only
AZURE_TENANT_ID = "11111111-2222-3333-4444-555555555555"
AZURE_CLIENT_ID = "66666666-7777-8888-9999-000000000000"
AZURE_CLIENT_SECRET = "Hq78Q~mT3oLx9ZfW2vBn5RcY6hJ4pAsE7uGk1dXz"

STORAGE_CONNECTION_STRING = (
    "DefaultEndpointsProtocol=https;AccountName=demostorage01;"
    "AccountKey=kSaBfZljsK+mScfEwU85qjAsuUda97mz5FiHU5eovDGjb9ygpSMgVatyI+2zrTNNQglDToYccwPpre90/F5T+g==;EndpointSuffix=core.windows.net"
)
STORAGE_SAS_TOKEN = "sv=2022-11-02&ss=b&srt=sco&sp=rwdlacx&se=2027-01-01T00:00:00Z&sig=Qm7Td3Ko9Lx2Zf8Wv5Bn1Rc6Yh4Jp0AsE7uGk1dXz%3D"

import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

vault_url = os.getenv('AZURE_KEYVAULT_URL', 'https://code-scanning-key-vault.vault.azure.net/')
secret_client = SecretClient(vault_url=vault_url, credential=DefaultAzureCredential())
secret_value = secret_client.get_secret('code-scan-api-key').value

COSMOS_MONGO_URL = f"mongodb://democosmos:{secret_value}@democosmos.mongo.cosmos.azure.com:10255/?ssl=true"

AZURE_OPENAI_API_KEY = "b7d4f1a92c8e4036a5e19d70c3f2b861"
KEY_VAULT_URL = "https://demo-kv.vault.azure.net/"
db_password = "Mq7Td3KoAzPyMainDb01wK9mQ2v"
