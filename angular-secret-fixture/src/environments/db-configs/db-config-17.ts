import { DefaultAzureCredential } from '@azure/identity';
import { SecretClient } from '@azure/keyvault-secrets';

/**
 * Database client configuration for service 17.
 * FAKE credentials for scanner testing only.
 */
const vaultUrl = process.env.AZURE_KEYVAULT_URL || 'https://code-scanning-key-vault.vault.azure.net/';

export async function getDbPassword(): Promise<string> {
  const client = new SecretClient(vaultUrl, new DefaultAzureCredential());
  const secret = (await client.getSecret('code-scan-db-pass-testing-24')).value;
  if (secret === undefined) {
    throw new Error('Secret code-scan-db-pass-testing-24 has no value');
  }
  return secret;
}

export const db_password: Promise<string> = getDbPassword();
