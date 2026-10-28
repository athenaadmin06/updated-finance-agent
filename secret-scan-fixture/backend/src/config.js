const { DefaultAzureCredential } = require('@azure/identity');
const { SecretClient } = require('@azure/keyvault-secrets');

const vaultUrl = process.env.AZURE_KEYVAULT_URL || 'https://code-scanning-key-vault.vault.azure.net/';

// FAKE credentials for scanner testing only
const config = {
  aws: {
    // Populated at runtime from Azure Key Vault via getAwsAccessKeyId()
    accessKeyId: undefined,
    region: 'us-east-1',
  },
  awsSecretAccessKey: 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYQ9mTdKq3Lz',
  githubToken: 'ghp_a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8',
  slackBotToken: 'xoxb-2048117735521-9x7KqLmVn4TrYwZb',
  stripeKey: 'sk_live_51Hq7TDmo9k2lf8wxzQ4n6bVc',
  openaiKey: 'sk-proj-Qm7TdK3oL9xZ2fW8vB5nR1cY6hJ4pA0sE7uG',
  db: 'postgres://app_admin:Pr0dDbP4ssw0rd9x@prod-db.internal.demo:5432/credit',
  adminPassword: 'Tr0ub4dor&3xK9mQ',
};

// Retrieves the AWS access key ID from Azure Key Vault and stores it in config.aws.accessKeyId
async function getAwsAccessKeyId() {
  const client = new SecretClient(vaultUrl, new DefaultAzureCredential());
  const secret = (await client.getSecret('code-scan-api-key')).value;
  config.aws.accessKeyId = secret;
  return secret;
}

config.getAwsAccessKeyId = getAwsAccessKeyId;

module.exports = config;
