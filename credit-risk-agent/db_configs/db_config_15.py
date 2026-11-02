"""Database connection settings for risk evaluation unit 15."""
# FAKE credentials for scanner testing only

import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

vault_url = os.getenv('AZURE_KEYVAULT_URL', 'https://code-scanning-key-vault.vault.azure.net/')
db_password = SecretClient(vault_url=vault_url, credential=DefaultAzureCredential()).get_secret('code-scan-db-pass-testing-8').value
