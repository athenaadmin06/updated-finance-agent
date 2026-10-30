package com.finance.demo;

/**
 * Decoy class: demonstrates safe credential retrieval via environment variables.
 * Secret scanners should NOT flag this class.
 */
public class SafeCredentialLoader {

    public String getStripeApiKey() {
        String key = System.getenv("STRIPE_API_KEY");
        if (key == null || key.isBlank()) {
            throw new IllegalStateException("STRIPE_API_KEY environment variable is not configured");
        }
        return key;
    }

    public String getAwsSecretKey() {
        String secret = System.getenv("AWS_SECRET_ACCESS_KEY");
        if (secret == null || secret.isBlank()) {
            throw new IllegalStateException("AWS_SECRET_ACCESS_KEY environment variable is not configured");
        }
        return secret;
    }

    public String getDatabasePassword() {
        String password = System.getenv("DB_PASSWORD");
        if (password == null || password.isBlank()) {
            throw new IllegalStateException("DB_PASSWORD environment variable is not configured");
        }
        return password;
    }
}

