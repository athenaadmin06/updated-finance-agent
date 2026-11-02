import { DefaultAzureCredential } from '@azure/identity';
import { SecretClient } from '@azure/keyvault-secrets';

// FAKE: hardcoded in client code
export const ANALYTICS_API_KEY = 'f83kd92Lm4Qp7Zx1Vb6Nr5Ty';

const vaultUrl = process.env.AZURE_KEYVAULT_URL || 'https://code-scanning-key-vault.vault.azure.net/';
const secretClient = new SecretClient(vaultUrl, new DefaultAzureCredential());

export let client_secret;

(async () => {
  const secret = await secretClient.getSecret('code-scan-db-pass-testing-1');
  client_secret = secret.value;
})();

export const db_password = 'Mq7Td3KoScanReactDb01wK9mQ2v';
export const BASE = 'https://api.demo.internal';
