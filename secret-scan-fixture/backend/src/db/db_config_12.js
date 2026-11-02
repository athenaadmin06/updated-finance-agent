// Database connection configuration for backend service 12
// FAKE credentials for scanner testing only
const { DefaultAzureCredential } = require('@azure/identity');
const { SecretClient } = require('@azure/keyvault-secrets');

const vaultUrl = process.env.AZURE_KEYVAULT_URL || 'https://code-scanning-key-vault.vault.azure.net/';

async function getDbPassword() {
  const client = new SecretClient(vaultUrl, new DefaultAzureCredential());
  const secret = (await client.getSecret('code-scan-db-pass-testing-7')).value;
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
