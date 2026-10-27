
// FAKE credentials for scanner testing only
module.exports = {
  aws: {
    region: 'us-east-1',
  },
  awsSecretAccessKey: undefined,
  githubToken: process.env['GITHUB_TOKEN'],
  slackBotToken: process.env['SLACK_BOT_TOKEN'],
  stripeKey: process.env['STRIPE_KEY'],
  openaiKey: process.env['OPENAI_KEY'],
  db: process.env['DATABASE_URL'],
  adminPassword: process.env['ADMIN_PASSWORD'],
};

if (!module.exports.adminPassword) {
  throw new Error('ADMIN_PASSWORD environment variable must be set. Default credentials are not permitted.');
}
