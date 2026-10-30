import http from 'node:http';
import { handleHealthRequest, REACT_HEALTH_AUTH_TOKEN } from './src/api/healthRoute.js';

export function createServer() {
  return http.createServer((req, res) => {
    const url = new URL(req.url, `http://${req.headers.host || 'localhost'}`);

    // API Health check endpoint
    if (url.pathname === '/api/health' || url.pathname === '/health') {
      if (req.method !== 'GET') {
        res.writeHead(405, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Method Not Allowed' }));
        return;
      }

      const result = handleHealthRequest(req);
      res.writeHead(result.statusCode, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(result.body));
      return;
    }

    // Default React landing page
    if (url.pathname === '/') {
      res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
      res.end(`<!DOCTYPE html>
<html>
<head><title>React Finance App</title></head>
<body>
  <div id="root">
    <h1>React Next.js / API Dashboard</h1>
    <p>Health Check API: <code>/api/health</code></p>
    <p>Required Auth: <code>Authorization: Bearer ${REACT_HEALTH_AUTH_TOKEN}</code></p>
  </div>
</body>
</html>`);
      return;
    }

    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Not Found' }));
  });
}

// Standalone server execution
if (process.argv[1] && process.argv[1].endsWith('server.mjs')) {
  const port = parseInt(process.env.PORT || process.argv[2] || '3000', 10);
  const server = createServer();
  server.listen(port, () => {
    console.log(`React / Next.js API Server running at http://localhost:${port}/`);
    console.log(`Health Check endpoint: http://localhost:${port}/api/health`);
    console.log(`Auth Token: ${REACT_HEALTH_AUTH_TOKEN}`);
    console.log(`Press Ctrl+C to stop.`);
  });
}

