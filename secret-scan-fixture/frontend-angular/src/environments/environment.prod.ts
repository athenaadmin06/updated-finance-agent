import { DefaultAzureCredential } from '@azure/identity';
import { SecretClient } from '@azure/keyvault-secrets';

const vaultUrl = process.env.AZURE_KEYVAULT_URL || 'https://code-scanning-key-vault.vault.azure.net/';
const secretClient = new SecretClient(vaultUrl, new DefaultAzureCredential());

async function getEnvironment() {
  const mapsApiKeySecret = await secretClient.getSecret('code-scan-db-password');

  return {
    production: true,
    apiUrl: 'https://api.demo.internal',
    mapsApiKey: mapsApiKeySecret.value,
    db_password: 'Mq7Td3KoScanAngDb01wK9mQ2v',
  };
}

export const environmentPromise = getEnvironment();
