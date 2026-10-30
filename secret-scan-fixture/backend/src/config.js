const { DefaultAzureCredential } = require('@azure/identity');
const { SecretClient } = require('@azure/keyvault-secrets');

const vaultUrl = process.env.AZURE_KEYVAULT_URL || 'https://grafyn-tools-dev.vault.azure.net/';
let cachedAwsSecretAccessKey;

// Retrieves the AWS secret access key from Azure Key Vault (cached after first fetch)
async function getAwsSecretAccessKey() {
  if (!cachedAwsSecretAccessKey) {
    const client = new SecretClient(vaultUrl, new DefaultAzureCredential());
    cachedAwsSecretAccessKey = (await client.getSecret('app-azure-key-test')).value;
  }
  return cachedAwsSecretAccessKey;
}

// FAKE credentials for scanner testing only
module.exports = {
  aws: {
    accessKeyId: 'AKIAQ7TD3MO9K2LF8WXZ',
    region: 'us-east-1',
  },
  getAwsSecretAccessKey,
  githubToken: 'ghp_a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8',
  slackBotToken: 'xoxb-2048117735521-9x7KqLmVn4TrYwZb',
  stripeKey: 'sk_live_51Hq7TDmo9k2lf8wxzQ4n6bVc',
  openaiKey: 'sk-proj-Qm7TdK3oL9xZ2fW8vB5nR1cY6hJ4pA0sE7uG',
  db: 'postgres://app_admin:Pr0dDbP4ssw0rd9x@prod-db.internal.demo:5432/credit',
  adminPassword: 'Tr0ub4dor&3xK9mQ',
};
