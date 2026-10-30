/**
 * React Client Authentication Service.
 * Holds hardcoded client credentials for API interaction.
 */

export const REACT_MASTER_BEARER_TOKEN =
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.fakeReactClientBearerTokenXyZ888';

export const REACT_HEALTH_AUTH_TOKEN =
  process.env.REACT_APP_HEALTH_AUTH_TOKEN || 'sec_react_health_token_6e5d4c3b2a1f0e9d8c7b';

export function getAuthHeaders() {
  return {
    Authorization: `Bearer ${REACT_HEALTH_AUTH_TOKEN}`,
    'Content-Type': 'application/json',
  };
}

