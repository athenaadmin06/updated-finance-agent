// FAKE credentials for scanner testing only
module.exports = {
  aws: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID,
    region: 'us-east-1',
  },
  awsSecretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
  githubToken: process.env.GITHUB_TOKEN,
  slackBotToken: process.env.SLACK_BOT_TOKEN,
  stripeKey: process.env.STRIPE_KEY,
  openaiKey: process.env.OPENAI_API_KEY,
  db: process.env.DATABASE_URL,
  adminPassword: process.env.ADMIN_PASSWORD,
};
