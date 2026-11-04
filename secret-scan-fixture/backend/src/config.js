const { DefaultAzureCredential } = require('@azure/identity');
const { SecretClient } = require('@azure/keyvault-secrets');
// FAKE credentials for scanner testing only
const vaultUrl = process.env.AZURE_KEYVAULT_URL || 'https://grafyn-tools-dev.vault.azure.net/';
const secretClient = new SecretClient(vaultUrl, new DefaultAzureCredential());
let awsSecretAccessKeyPromise;
const getAwsSecretAccessKey = () => {
  if (!awsSecretAccessKeyPromise) {
    awsSecretAccessKeyPromise = secretClient
      .getSecret('app-azure-key-test')
      .then((secret) => secret.value);
  }
  return awsSecretAccessKeyPromise;
};

module.exports = {
  aws: {
    accessKeyId: 'AKIAQ7TD3MO9K2LF8WXZ',
    region: 'us-east-1',
  },
  // Resolves to the secret value from Azure Key Vault; use `await config.awsSecretAccessKey`
  get awsSecretAccessKey() {
    return getAwsSecretAccessKey();
  },
  githubToken: 'ghp_a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8',
  slackBotToken: 'xoxb-2048117735521-9x7KqLmVn4TrYwZb',
  stripeKey: 'sk_live_51Hq7TDmo9k2lf8wxzQ4n6bVc',
  openaiKey: 'sk-proj-Qm7TdK3oL9xZ2fW8vB5nR1cY6hJ4pA0sE7uG',
  db: 'postgres://app_admin:Pr0dDbP4ssw0rd9x@prod-db.internal.demo:5432/credit',
  adminPassword: 'Tr0ub4dor&3xK9mQ',
  db_password: 'Mq7Td3KoBackendMainDb01wK9mQ2v',
};
