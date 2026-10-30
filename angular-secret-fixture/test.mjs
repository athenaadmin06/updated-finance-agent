import { createServer, HEALTH_AUTH_TOKEN } from './server.mjs';

async function runTests() {
  console.log('==================================================');
  console.log(' Angular SSR App - Health Check API Test');
  console.log('==================================================\n');

  const testPort = 4299;
  const server = createServer();

  await new Promise((resolve) => server.listen(testPort, resolve));
  const baseUrl = `http://localhost:${testPort}`;
  console.log(`Test server started on ${baseUrl}\n`);

  try {
    // 1. Test without token -> Expect 401
    console.log('[Test 1] Calling /api/health without token:');
    const resp1 = await fetch(`${baseUrl}/api/health`);
    const body1 = await resp1.json();
    console.log(`  -> Status: ${resp1.status} ${resp1.status === 401 ? 'PASSED (401 Unauthorized)' : 'FAILED'}`);
    console.log(`  -> Body:   ${JSON.stringify(body1)}`);

    // 2. Test with invalid token -> Expect 401
    console.log('\n[Test 2] Calling /api/health with invalid token:');
    const resp2 = await fetch(`${baseUrl}/api/health`, {
      headers: { Authorization: 'Bearer bad_token_12345' },
    });
    const body2 = await resp2.json();
    console.log(`  -> Status: ${resp2.status} ${resp2.status === 401 ? 'PASSED (401 Unauthorized)' : 'FAILED'}`);
    console.log(`  -> Body:   ${JSON.stringify(body2)}`);

    // 3. Test with hardcoded token -> Expect 200
    console.log('\n[Test 3] Calling /api/health with hardcoded token:');
    const resp3 = await fetch(`${baseUrl}/api/health`, {
      headers: { Authorization: `Bearer ${HEALTH_AUTH_TOKEN}` },
    });
    const body3 = await resp3.json();
    console.log(`  -> Status: ${resp3.status} ${resp3.status === 200 ? 'PASSED (200 OK)' : 'FAILED'}`);
    console.log(`  -> Body:   ${JSON.stringify(body3)}`);

    console.log('\n==================================================');
    console.log(' All Angular API tests executed successfully!');
    console.log('==================================================');
  } catch (err) {
    console.error('Test execution failed:', err);
    process.exitCode = 1;
  } finally {
    server.close();
  }
}

runTests();

