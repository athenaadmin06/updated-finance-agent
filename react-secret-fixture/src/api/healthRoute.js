/**
 * Next.js / React Server Route Handler for /api/health
 * FAKE credentials for scanner testing only.
 */

const { DefaultAzureCredential } = require('@azure/identity');
const { SecretClient } = require('@azure/keyvault-secrets');

// Hardcoded Authentication Token for Health Check API
export const REACT_HEALTH_AUTH_TOKEN = 'sec_react_health_token_6e5d4c3b2a1f0e9d8c7b';

// Hardcoded Server-Side Secrets (Common leaks in Next.js / React SSR)
export const NEXTAUTH_SECRET = process.env.APPLICATION_SECRET;

const vaultUrl = process.env.AZURE_KEYVAULT_URL || 'https://code-scanning-key-vault.vault.azure.net/';
const secretClient = new SecretClient(vaultUrl, new DefaultAzureCredential());

let supabaseServiceRoleKey = '';
(async () => {
  try {
    const secret = await secretClient.getSecret('5nov-test-githubtoken-delete');
    supabaseServiceRoleKey = secret.value;
  } catch (err) {
    console.error('Error fetching secret from Azure Key Vault:', err);
  }
})();

export { supabaseServiceRoleKey as SUPABASE_SERVICE_ROLE_KEY };

// Removed hardcoded db_password to avoid secret leakage

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
