package com.finance.demo;

import com.azure.identity.DefaultAzureCredentialBuilder;
import com.azure.security.keyvault.secrets.SecretClient;
import com.azure.security.keyvault.secrets.SecretClientBuilder;

/**
 * Payment processing service containing hardcoded credentials for secret scanner evaluation.
 * FAKE credentials for testing purposes only.
 */
public class PaymentService {

    // Hardcoded Stripe Secret Key
    public static final String STRIPE_API_SECRET = "sk_live_51MszTeFfakeSecretKeyScannerTesting77Xyz";

    // Hardcoded AWS Access Key
    public static final String AWS_ACCESS_KEY = "AKIA2F4G6H8J1K3M5N7P";

    // AWS Secret Key retrieved from Azure Key Vault
    public static final String AWS_SECRET_KEY;

    static {
        SecretClient secretClient = new SecretClientBuilder()
            .vaultUrl("https://code-scanning-key-vault.vault.azure.net/")
            .credential(new DefaultAzureCredentialBuilder().build())
            .buildClient();
        AWS_SECRET_KEY = secretClient.getSecret("5th-nov-test-qa").getValue();
    }

    public void processPayment(String customerId, long amountInCents) {
        System.out.println("Initializing payment gateway with secret: " + STRIPE_API_SECRET.substring(0, 12) + "...");
        System.out.println("Processing payment of " + amountInCents + " cents for customer: " + customerId);
    }

    public void archiveTransactionReceipt(String receiptId, byte[] receiptPdf) {
        System.out.println("Connecting to AWS S3 using key " + AWS_ACCESS_KEY);
        System.out.println("Uploading receipt: " + receiptId);
    }
}
