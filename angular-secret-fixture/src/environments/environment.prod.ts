/**
 * Angular Production Environment Configuration
 * FAKE credentials representing dangerous client-side secrets commonly flagged by scanners.
 */
export const environment = {
  production: true,
  apiUrl: 'https://api.finance.internal',

  // Leak 1: Stripe Secret Key (Dangerous client-side leak)
  stripeSecretKey: 'sk_live_51AngularFinanceFakeStripeSecretKey88Xyz',

  // Leak 2: AWS S3 Access & Secret Keys
  awsAccessKey: 'AKIA8ANGULAR7EXAMPLE66',
  awsSecretKey: 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYAngularKey66',

  // Leak 3: Google Maps API Key
  mapsApiKey: 'AIzaSyD-7xK9mP3qR5tV8yB1cE4gH7jL0nQ3sU6',

  // Leak 4: Firebase Config / Token
  firebaseApiKey: 'AIzaSyB8uK7lM2nO4pQ6rS8tU0vW2xY4zA1bC3d',

  // Health API Token used by Angular HTTP client
  healthAuthToken: 'sec_angular_health_token_7d6c5b4a3e2f1a0b9c8d',
};

