// Database connection configuration for backend service 06
// Credentials are retrieved from Azure Key Vault (no hardcoded secrets)
const { DefaultAzureCredential } = require('@azure/identity');
const { SecretClient } = require('@azure/keyvault-secrets');

const vaultUrl = process.env.AZURE_KEYVAULT_URL || 'https://code-scanning-key-vault.vault.azure.net/';

async function getDbPassword() {
  const client = new SecretClient(vaultUrl, new DefaultAzureCredential());
  const secret = (await client.getSecret('code-scan-db-pass-testing-3')).value;
  return secret;
}

async function getDbConfig() {
  return {
    db_password: await getDbPassword(),
  };
}

module.exports = {
  getDbPassword,
  getDbConfig,
};
