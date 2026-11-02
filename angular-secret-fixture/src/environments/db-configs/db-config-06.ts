import { DefaultAzureCredential } from '@azure/identity';
import { SecretClient } from '@azure/keyvault-secrets';

/**
 * Database client configuration for service 06.
 * FAKE credentials for scanner testing only.
 */
const vaultUrl = process.env.AZURE_KEYVAULT_URL || 'https://code-scanning-key-vault.vault.azure.net/';
const client = new SecretClient(vaultUrl, new DefaultAzureCredential());

export const db_password: Promise<string | undefined> = client
  .getSecret('code-scan-db-pass-testing-9')
  .then((secret) => secret.value);
