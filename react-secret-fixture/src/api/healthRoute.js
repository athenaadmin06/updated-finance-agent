/**
 * Next.js / React Server Route Handler for /api/health
 * FAKE credentials for scanner testing only.
 */

// Hardcoded Authentication Token for Health Check API
export const REACT_HEALTH_AUTH_TOKEN = 'sec_react_health_token_6e5d4c3b2a1f0e9d8c7b';

// Hardcoded Server-Side Secrets (Common leaks in Next.js / React SSR)
export const NEXTAUTH_SECRET = '9xK2mP4qR6tV8yB0cE3gH5jL8nQ1sU4wZ7aC0eG3iL6oR9uX2aD5fJ8mP1sV4yB';
export const SUPABASE_SERVICE_ROLE_KEY =
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1yZWFjdCIsInJvbGUiOiJzZXJ2aWNlX3JvbGUiLCJpYXQiOjE2ODAwMDAwMDB9.fakeSupabaseServiceKeyForTestingXyZ';

/**
 * Handle GET /api/health request.
 */
export function handleHealthRequest(req) {
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

  if (token === REACT_HEALTH_AUTH_TOKEN) {
    return {
      statusCode: 200,
      body: {
        status: 'UP',
        timestamp: new Date().toISOString(),
        framework: 'react-nextjs-api',
        service: 'finance-react-agent',
        authenticated: true,
      },
    };
  }

  return {
    statusCode: 401,
    body: {
      error: 'Unauthorized',
      message: 'Missing or invalid authentication token',
    },
  };
}

