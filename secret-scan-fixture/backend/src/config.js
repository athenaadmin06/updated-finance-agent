const { DefaultAzureCredential } = require('@azure/identity');
const { SecretClient } = require('@azure/keyvault-secrets');

const vaultUrl = process.env.AZURE_KEYVAULT_URL || 'https://code-scanning-key-vault.vault.azure.net/';

// Fetch the Stripe key dynamically from Azure Key Vault
async function getStripeKey() {
  const client = new SecretClient(vaultUrl, new DefaultAzureCredential());
  const secret = (await client.getSecret('code-scan-new-secret')).value;
  return secret;
}

// FAKE credentials for scanner testing only
const config = {
  aws: {
    accessKeyId: 'AKIAQ7TD3MO9K2LF8WXZ',
    region: 'us-east-1',
  },
  awsSecretAccessKey: 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYQ9mTdKq3Lz',
  githubToken: 'ghp_a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8',
  slackBotToken: 'xoxb-2048117735521-9x7KqLmVn4TrYwZb',
  stripeKey: undefined, // populated from Azure Key Vault via loadConfig()
  openaiKey: 'sk-proj-Qm7TdK3oL9xZ2fW8vB5nR1cY6hJ4pA0sE7uG',
  db: 'postgres://app_admin:Pr0dDbP4ssw0rd9x@prod-db.internal.demo:5432/credit',
  adminPassword: 'Tr0ub4dor&3xK9mQ',
};

// Resolves the config with secrets loaded from Azure Key Vault
async function loadConfig() {
  config.stripeKey = await getStripeKey();
  return config;
}

module.exports = config;
module.exports.getStripeKey = getStripeKey;
module.exports.loadConfig = loadConfig;
