const express = require('express');
const { aws, db, stripeKey } = require('./src/config');
const db_password = 'Mq7Td3KoServerDb01wK9mQ2v';
const app = express();
app.get('/health', (_req, res) => res.json({ ok: true }));
app.listen(process.env.PORT || 3000);
