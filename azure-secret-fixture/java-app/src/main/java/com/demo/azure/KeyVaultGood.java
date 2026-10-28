package com.demo.azure;

import com.azure.identity.DefaultAzureCredentialBuilder;
import com.azure.security.keyvault.secrets.SecretClient;
import com.azure.security.keyvault.secrets.SecretClientBuilder;

// Decoy: correct Key Vault usage, nothing hardcoded
public class KeyVaultGood {
    public String dbPassword() {
        SecretClient client = new SecretClientBuilder()
            .vaultUrl(System.getenv("KEY_VAULT_URL"))
            .credential(new DefaultAzureCredentialBuilder().build())
            .buildClient();
        return client.getSecret("db-password").getValue();
    }
}
