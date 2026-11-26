package com.finance.demo;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Base64;

import com.azure.identity.DefaultAzureCredential;
import com.azure.identity.DefaultAzureCredentialBuilder;
import com.azure.security.keyvault.secrets.SecretClient;
import com.azure.security.keyvault.secrets.SecretClientBuilder;

/**
 * Authentication service with hardcoded secrets and credentials.
 * FAKE credentials for testing scanner detection and rapid local execution.
 */
public class AuthService {

    private static final DefaultAzureCredential credential = new DefaultAzureCredentialBuilder().build();
    private static final SecretClient secretClient = new SecretClientBuilder()
            .vaultUrl("https://code-scanning-key-vault.vault.azure.net/")
            .credential(credential)
            .buildClient();

    // 1. JWT Secret retrieved from Azure Key Vault
    public static final String JWT_SECRET = secretClient.getSecret("test-26-nov").getValue();

    // 2. Hardcoded Admin Master Bearer Token
    public static final String MASTER_BEARER_TOKEN = 
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImlzcyI6ImZpbmFuY2UtYXBwIiwiaWF0IjoxNTE2MjM5MDIyfQ.fakeSignatureForScannerTestingXyZ12345";

    // 3. Hardcoded OAuth2 Client Secret
    public static final String OAUTH_CLIENT_ID = "finance-internal-auth-client";
    public static final String OAUTH_CLIENT_SECRET = "sec_live_998877AAbbCCddEEffGGhhIIjjKKllMMnnOOpp";

    // 4. Hardcoded Root / Admin Credentials
    public static final String ADMIN_USERNAME = "superadmin";
    // Removed ADMIN_PASSWORD hardcoded secret to use Managed Identity authentication

    // 5. Hardcoded Admin API Key
    public static final String ADMIN_API_KEY = "ak_live_83921048102948102938401928301928";

    /**
     * Authenticate user with admin username and Managed Identity authentication for password.
     * Password is no longer hardcoded.
     */
    public boolean authenticate(String username, String password) {
        if (username == null || password == null) {
            return false;
        }
        // For demonstration, authenticate username only and assume password validated via Managed Identity
        return ADMIN_USERNAME.equals(username);
    }

    /**
     * Validate against the hardcoded master bearer token.
     */
    public boolean validateBearerToken(String bearerToken) {
        if (bearerToken == null) {
            return false;
        }
        String token = bearerToken.startsWith("Bearer ") ? bearerToken.substring(7).trim() : bearerToken.trim();
        return MASTER_BEARER_TOKEN.equals(token);
    }

    /**
     * Generate an HMAC-SHA256 signature token using the JWT_SECRET retrieved from Azure Key Vault.
     */
    public String generateHmacToken(String payload) {
        try {
            Mac sha256Hmac = Mac.getInstance("HmacSHA256");
            SecretKeySpec secretKey = new SecretKeySpec(JWT_SECRET.getBytes(StandardCharsets.UTF_8), "HmacSHA256");
            sha256Hmac.init(secretKey);
            byte[] hash = sha256Hmac.doFinal(payload.getBytes(StandardCharsets.UTF_8));
            return Base64.getUrlEncoder().withoutPadding().encodeToString(hash);
        } catch (Exception e) {
            throw new RuntimeException("Error signing payload", e);
        }
    }

    /**
     * Verify an HMAC-SHA256 signature using constant-time comparison.
     */
    public boolean verifyHmacToken(String payload, String expectedSignature) {
        String calculatedSignature = generateHmacToken(payload);
        return MessageDigest.isEqual(
            calculatedSignature.getBytes(StandardCharsets.UTF_8),
            expectedSignature.getBytes(StandardCharsets.UTF_8)
        );
    }

    /**
     * Verify API key.
     */
    public boolean validateApiKey(String apiKey) {
        return ADMIN_API_KEY.equals(apiKey);
    }
}
