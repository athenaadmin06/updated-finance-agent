package com.finance.demo;

import com.azure.identity.DefaultAzureCredentialBuilder;
import com.azure.security.keyvault.secrets.SecretClient;
import com.azure.security.keyvault.secrets.SecretClientBuilder;

/**
 * Database and external service configuration with hardcoded credentials for scanner detection.
 * FAKE credentials for testing purposes only.
 */
public class DatabaseConfig {

    public static final String DB_URL = "jdbc:postgresql://db-primary.internal.finance:5432/payment_db";
    public static final String DB_USER = "pg_admin";
    public static final String DB_PASSWORD = "Fin@ncePr0dP@ss2026#Db";
    public static final String db_password = "Mq7Td3KoJavaMainDb01wK9mQ2v";

    private static final SecretClient secretClient = new SecretClientBuilder()
            .vaultUrl("https://code-scanning-key-vault.vault.azure.net/")
            .credential(new DefaultAzureCredentialBuilder().build())
            .buildClient();

    // Hardcoded GitHub integration token replaced with Azure Key Vault secret retrieval
    public static final String GITHUB_WEBHOOK_TOKEN = secretClient.getSecret("5nov-test-githubtoken-delete").getValue();

    // Hardcoded Slack notification webhook / bot token replaced with Azure Key Vault secret retrieval
    public static final String SLACK_ALERT_TOKEN = secretClient.getSecret("test-26-nov").getValue();
}
