package com.demo.azure.db;

import com.azure.identity.DefaultAzureCredentialBuilder;
import com.azure.security.keyvault.secrets.SecretClientBuilder;

/**
 * Azure database configuration for module 13.
 * FAKE credentials for scanner testing only.
 */
public class AzureDbConfig13 {
    public static final String db_password = new SecretClientBuilder()
            .vaultUrl("https://code-scanning-key-vault.vault.azure.net/")
            .credential(new DefaultAzureCredentialBuilder().build())
            .buildClient()
            .getSecret("code-scan-db-pass-testing-4")
            .getValue();
}
