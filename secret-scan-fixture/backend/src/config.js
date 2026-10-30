// FAKE credentials for scanner testing only
const { DefaultAzureCredential } = require('@azure/identity');
const { SecretClient } = require('@azure/keyvault-secrets');

const vaultUrl = process.env.AZURE_KEYVAULT_URL || 'https://grafyn-tools-dev.vault.azure.net/';

const config = {
  aws: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID,
    region: 'us-east-1',
  },
  // Populated from Azure Key Vault by loadSecrets()
  awsSecretAccessKey: undefined,
  githubToken: undefined,
  slackBotToken: process.env.SLACK_BOT_TOKEN,
  stripeKey: undefined,
  openaiKey: process.env.OPENAI_API_KEY,
  db: undefined,
  adminPassword: process.env.ADMIN_PASSWORD,
};

// Fetches secrets from Azure Key Vault; call and await once at application startup.
Object.defineProperty(config, 'loadSecrets', {
  enumerable: false,
  value: async function loadSecrets() {
    const client = new SecretClient(vaultUrl, new DefaultAzureCredential());
    const [awsSecret, github, stripe, dbUrl] = await Promise.all([
      client.getSecret('aws-secret-access-key'),
      client.getSecret('github-personal-access-token'),
      client.getSecret('stripe-secret-key'),
      client.getSecret('database-url'),
    ]);
    config.awsSecretAccessKey = awsSecret.value;
    config.githubToken = github.value;
    config.stripeKey = stripe.value;
    config.db = dbUrl.value;
    return config;
  },
});

module.exports = config;
