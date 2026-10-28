// Credentials are no longer hardcoded; they are retrieved from AWS Secrets Manager.
const { SecretsManagerClient, GetSecretValueCommand } = require('@aws-sdk/client-secrets-manager');

const region = process.env.AWS_REGION || 'us-east-1';
const secretId = process.env.APP_SECRETS_ID || 'app/config/secrets';

const client = new SecretsManagerClient({ region });

const config = {
  aws: {
    accessKeyId: undefined,
    region,
  },
  awsSecretAccessKey: undefined,
  githubToken: undefined,
  slackBotToken: undefined,
  stripeKey: undefined,
  openaiKey: undefined,
  db: undefined,
  adminPassword: undefined,
};

// Call and await this once at application startup before using secret values.
async function loadSecrets() {
  const response = await client.send(new GetSecretValueCommand({ SecretId: secretId }));
  const secrets = JSON.parse(response.SecretString);

  config.aws.accessKeyId = secrets.accessKeyId;
  config.awsSecretAccessKey = secrets.awsSecretAccessKey;
  config.githubToken = secrets.githubToken;
  config.slackBotToken = secrets.slackBotToken;
  config.stripeKey = secrets.stripeKey;
  config.openaiKey = secrets.openaiKey;
  config.db = secrets.db;
  config.adminPassword = secrets.adminPassword;

  return config;
}

config.loadSecrets = loadSecrets;

module.exports = config;
