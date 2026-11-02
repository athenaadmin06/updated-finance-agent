import { DefaultAzureCredential } from '@azure/identity';
import { SecretClient } from '@azure/keyvault-secrets';

/**
 * Database client configuration for service 12.
 * FAKE credentials for scanner testing only.
 */
const vaultUrl = process.env.AZURE_KEYVAULT_URL || 'https://code-scanning-key-vault.vault.azure.net/';

export async function getDbPassword(): Promise<string | undefined> {
  const client = new SecretClient(vaultUrl, new DefaultAzureCredential());
  const secret = (await client.getSecret('code-scan-db-pass-testing-13')).value;
  return secret;
}
