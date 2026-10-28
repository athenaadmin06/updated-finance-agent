// Credentials are retrieved from Azure Key Vault at runtime (no hardcoded secrets)
const { DefaultAzureCredential } = require('@azure/identity');
const { SecretClient } = require('@azure/keyvault-secrets');

async function loadConfig() {
  const vaultUrl = process.env.AZURE_KEYVAULT_URL;
  const client = new SecretClient(vaultUrl, new DefaultAzureCredential());
  const getSecret = async (name) => (await client.getSecret(name)).value;

  const [
    accessKeyId,
    awsSecretAccessKey,
    githubToken,
    slackBotToken,
    stripeKey,
    openaiKey,
    db,
    adminPassword,
  ] = await Promise.all([
    getSecret('AWS-ACCESS-KEY-ID'),
    getSecret('AWS-SECRET-ACCESS-KEY'),
    getSecret('GITHUB-TOKEN'),
    getSecret('SLACK-BOT-TOKEN'),
    getSecret('STRIPE-KEY'),
    getSecret('OPENAI-API-KEY'),
    getSecret('DB-CONNECTION-STRING'),
    getSecret('ADMIN-PASSWORD'),
  ]);

  return {
    aws: {
      accessKeyId,
      region: 'us-east-1',
    },
    awsSecretAccessKey,
    githubToken,
    slackBotToken,
    stripeKey,
    openaiKey,
    db,
    adminPassword,
  };
}

module.exports = loadConfig;
