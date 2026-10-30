package com.finance.demo;

/**
 * Payment processing service containing hardcoded credentials for secret scanner evaluation.
 * FAKE credentials for testing purposes only.
 */
public class PaymentService {

    // Hardcoded Stripe Secret Key
    public static final String STRIPE_API_SECRET = "sk_live_51MszTeFfakeSecretKeyScannerTesting77Xyz";

    // Hardcoded AWS Access & Secret Keys
    public static final String AWS_ACCESS_KEY = "AKIA2F4G6H8J1K3M5N7P";
    public static final String AWS_SECRET_KEY = "vN8xL2kP4mQ9rT1wZ3bC5dE7fG9hJ1kM3nO5pQ7r";

    public void processPayment(String customerId, long amountInCents) {
        System.out.println("Initializing payment gateway with secret: " + STRIPE_API_SECRET.substring(0, 12) + "...");
        System.out.println("Processing payment of " + amountInCents + " cents for customer: " + customerId);
    }

    public void archiveTransactionReceipt(String receiptId, byte[] receiptPdf) {
        System.out.println("Connecting to AWS S3 using key " + AWS_ACCESS_KEY);
        System.out.println("Uploading receipt: " + receiptId);
    }
}

