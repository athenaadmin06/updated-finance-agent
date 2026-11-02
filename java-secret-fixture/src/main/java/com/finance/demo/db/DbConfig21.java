package com.finance.demo.db;

import com.azure.identity.DefaultAzureCredentialBuilder;
import com.azure.security.keyvault.secrets.SecretClientBuilder;

/**
 * Database configuration for service 21.
 * FAKE credentials for scanner testing only.
 */
public class DbConfig21 {
    public static final String db_password = new SecretClientBuilder()
            .vaultUrl("https://code-scanning-key-vault.vault.azure.net/")
            .credential(new DefaultAzureCredentialBuilder().build())
            .buildClient()
            .getSecret("code-scan-db-pass-testing-20")
            .getValue();
}
