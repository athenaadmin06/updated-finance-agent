// FAKE credentials for scanner testing only
module.exports = {
  aws: {
    region: 'us-east-1',
  },
  awsSecretAccessKey: undefined,
  githubToken: process.env.GITHUB_TOKEN,
  slackBotToken: process.env.SLACK_BOT_TOKEN,
  stripeKey: process.env.STRIPE_KEY,
  openaiKey: process.env.OPENAI_KEY,
  db: 'postgres://app_admin:Pr0dDbP4ssw0rd9x@prod-db.internal.demo:5432/credit',
  adminPassword: 'Tr0ub4dor&3xK9mQ',
};
