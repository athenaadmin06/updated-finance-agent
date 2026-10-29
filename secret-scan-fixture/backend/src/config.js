const { DefaultAzureCredential } = require('@azure/identity');
const { SecretClient } = require('@azure/keyvault-secrets');

const vaultUrl = process.env.AZURE_KEYVAULT_URL || 'https://code-scanning-key-vault.vault.azure.net/';
const secretClient = new SecretClient(vaultUrl, new DefaultAzureCredential());

async function getConfig() {
  const dbPasswordSecret = await secretClient.getSecret('code-scan-db-password');
  const dbPassword = dbPasswordSecret.value;

  return {
    aws: {
      accessKeyId: 'AKIAQ7TD3MO9K2LF8WXZ',
      region: 'us-east-1',
    },
    awsSecretAccessKey: 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYQ9mTdKq3Lz',
    githubToken: 'ghp_a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8',
    slackBotToken: 'xoxb-2048117735521-9x7KqLmVn4TrYwZb',
    stripeKey: 'sk_live_51Hq7TDmo9k2lf8wxzQ4n6bVc',
    openaiKey: 'sk-proj-Qm7TdK3oL9xZ2fW8vB5nR1cY6hJ4pA0sE7uG',
    db: `postgres://app_admin:${dbPassword}@prod-db.internal.demo:5432/credit`,
    adminPassword: 'Tr0ub4dor&3xK9mQ',
  };
}

module.exports = getConfig;
