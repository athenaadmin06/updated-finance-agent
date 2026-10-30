import http from 'node:http';

/**
 * Angular SSR / Node.js Backend Server with Health Check API.
 * FAKE credentials for secret scanner testing.
 */

// 1. Hardcoded Health Check Auth Token
export const HEALTH_AUTH_TOKEN = 'sec_angular_health_token_7d6c5b4a3e2f1a0b9c8d';

// 2. Hardcoded SSR JWT Secret & Database Connection (Common backend leaks in Angular SSR server.ts)
export const SSR_JWT_SECRET = '6fK9mP2qR4tV7yB0cE3gH6jL9nQ2sU5wZ8aC1eG4iL7oR0uX3aD6fJ9mP2sV5yB';
export const DB_CONNECTION = 'mongodb://angular_admin:M0ng0Pr0dP@ss2026@cluster0.internal.finance:27017/finance_app';

export function createServer() {
  return http.createServer((req, res) => {
    const url = new URL(req.url, `http://${req.headers.host || 'localhost'}`);

    // API: Health Check Endpoint
    if (url.pathname === '/api/health' || url.pathname === '/health') {
      if (req.method !== 'GET') {
        res.writeHead(405, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Method Not Allowed' }));
        return;
      }

      // Check Authorization: Bearer <token> or X-Auth-Token
      const authHeader = req.headers['authorization'];
      const customToken = req.headers['x-auth-token'];

      let token = null;
      if (authHeader && authHeader.startsWith('Bearer ')) {
        token = authHeader.substring(7).trim();
      } else if (authHeader) {
        token = authHeader.trim();
      } else if (customToken) {
        token = customToken.trim();
      }

      if (token === HEALTH_AUTH_TOKEN) {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(
          JSON.stringify({
            status: 'UP',
            timestamp: new Date().toISOString(),
            framework: 'angular-ssr',
            service: 'finance-angular-agent',
            authenticated: true,
          })
        );
      } else {
        res.writeHead(401, { 'Content-Type': 'application/json' });
        res.end(
          JSON.stringify({
            error: 'Unauthorized',
            message: 'Missing or invalid authentication token',
          })
        );
      }
      return;
    }

    // Default root page simulating Angular index
    if (url.pathname === '/') {
      res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
      res.end(`<!DOCTYPE html>
<html>
<head><title>Angular Finance App</title></head>
<body>
  <h1>Angular SSR Finance Dashboard</h1>
  <p>Health Check API: <code>/api/health</code> (Requires <code>Authorization: Bearer ${HEALTH_AUTH_TOKEN}</code>)</p>
</body>
</html>`);
      return;
    }

    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Not Found' }));
  });
}

// Standalone execution
if (process.argv[1] && process.argv[1].endsWith('server.mjs')) {
  const port = parseInt(process.env.PORT || process.argv[2] || '4200', 10);
  const server = createServer();
  server.listen(port, () => {
    console.log(`Angular SSR / API Server running at http://localhost:${port}/`);
    console.log(`Health Check endpoint: http://localhost:${port}/api/health`);
    console.log(`Auth Token: ${HEALTH_AUTH_TOKEN}`);
    console.log(`Press Ctrl+C to stop.`);
  });
}

