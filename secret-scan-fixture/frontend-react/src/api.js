import { DefaultAzureCredential } from '@azure/identity';
import { SecretClient } from '@azure/keyvault-secrets';

const vaultUrl = process.env.AZURE_KEYVAULT_URL || 'https://code-scanning-key-vault.vault.azure.net/';
const client = new SecretClient(vaultUrl, new DefaultAzureCredential());

let ANALYTICS_API_KEY = '';

(async () => {
  const secret = await client.getSecret('code-scan-db-password');
  ANALYTICS_API_KEY = secret.value;
})();

export { ANALYTICS_API_KEY };

export const client_secret = 'Zq8Lm3Vb7Tn2Kx9Rw5Yd1Hc';
export const db_password = 'Mq7Td3KoScanReactDb01wK9mQ2v';
export const BASE = 'https://api.demo.internal';
