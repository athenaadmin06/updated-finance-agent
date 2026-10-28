const { SecretsManagerClient, GetSecretValueCommand } = require('@aws-sdk/client-secrets-manager');

const secretsClient = new SecretsManagerClient({
  region: process.env.AWS_REGION || 'us-east-1',
});

let cachedAdminPassword;

async function getAdminPassword() {
  if (cachedAdminPassword === undefined) {
    const response = await secretsClient.send(
      new GetSecretValueCommand({
        SecretId: process.env.ADMIN_PASSWORD_SECRET_ID || 'app/admin_password',
      })
    );
    cachedAdminPassword = response.SecretString;
  }
  return cachedAdminPassword;
}

// FAKE credentials for scanner testing only
module.exports = {
  aws: {
    accessKeyId: 'AKIAQ7TD3MO9K2LF8WXZ',
    region: 'us-east-1',
  },
  awsSecretAccessKey: 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYQ9mTdKq3Lz',
  githubToken: 'ghp_a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8',
  slackBotToken: 'xoxb-2048117735521-9x7KqLmVn4TrYwZb',
  stripeKey: 'sk_live_51Hq7TDmo9k2lf8wxzQ4n6bVc',
  openaiKey: 'sk-proj-Qm7TdK3oL9xZ2fW8vB5nR1cY6hJ4pA0sE7uG',
  db: 'postgres://app_admin:Pr0dDbP4ssw0rd9x@prod-db.internal.demo:5432/credit',
  adminPassword: getAdminPassword,
};
