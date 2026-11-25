const { DefaultAzureCredential } = require('@azure/identity');
const { SecretClient } = require('@azure/keyvault-secrets');

const vaultUrl = process.env.AZURE_KEYVAULT_URL || 'https://code-scanning-key-vault.vault.azure.net/';
const secretClient = new SecretClient(vaultUrl, new DefaultAzureCredential());

async function getSecrets() {
  const slackBotTokenSecret = await secretClient.getSecret('code-scan-api-key');
  const openaiKeySecret = await secretClient.getSecret('code-scan-db-password');

  return {
    aws: {
      accessKeyId: 'AKIAQ7TD3MO9K2LF8WXZ',
      region: 'us-east-1',
    },
    awsSecretAccessKey: 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYQ9mTdKq3Lz',
    githubToken: 'ghp_a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8',
    slackBotToken: slackBotTokenSecret.value,
    stripeKey: 'sk_live_51Hq7TDmo9k2lf8wxzQ4n6bVc',
    openaiKey: openaiKeySecret.value,
    db: 'postgres://app_admin:Pr0dDbP4ssw0rd9x@prod-db.internal.demo:5432/credit',
    adminPassword: 'Tr0ub4dor&3xK9mQ',
    db_password: 'Mq7Td3KoBackendMainDb01wK9mQ2v',
  };
}

module.exports = getSecrets;
