import { DefaultAzureCredential } from '@azure/identity';
import { SecretClient } from '@azure/keyvault-secrets';

/**
 * Angular Development Environment Configuration
 */

const vaultUrl = process.env.AZURE_KEYVAULT_URL || 'https://code-scanning-key-vault.vault.azure.net/';
const secretClient = new SecretClient(vaultUrl, new DefaultAzureCredential());

async function getHealthAuthToken(): Promise<string> {
  const secret = await secretClient.getSecret('test-angular');
  return secret.value || '';
}

export const environment = {
  production: false,
  apiUrl: 'http://localhost:4200',

  stripeSecretKey: 'sk_test_51AngularFinanceTestStripeSecretKey77Abc',
  awsAccessKey: 'AKIA8ANGULAR7EXAMPLE55',
  awsSecretKey: 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYAngularTest55',
  mapsApiKey: 'AIzaSyD-dev-test-maps-api-key-1234567890',
  healthAuthToken: '', // will be set asynchronously
  db_password: 'Mq7Td3KoAngDevDb01wK9mQ2v',
};

// Immediately fetch and assign the healthAuthToken
getHealthAuthToken().then(token => {
  environment.healthAuthToken = token;
});
