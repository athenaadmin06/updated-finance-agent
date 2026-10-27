// Decoys: none of these should be reported
const apiKey = process.env.OPENAI_API_KEY;
const password = "changeme";
const token = "<your-token-here>";
const secret = "${DB_SECRET}";
module.exports = { apiKey, password, token, secret };
