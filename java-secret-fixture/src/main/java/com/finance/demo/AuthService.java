package com.finance.demo;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Base64;

/**
 * Authentication service with hardcoded secrets and credentials.
 * FAKE credentials for testing scanner detection and rapid local execution.
 */
public class AuthService {

    // 1. Hardcoded HMAC-SHA256 Secret Key (High-entropy secret string)
    public static final String JWT_SECRET = "4eC8k9P2mZ5rT7wX1vY3bQ6sD8fH0jL2nN4pQ6rS8tU0vW2xY4zA1bC3dE5fG7h";

    // 2. Hardcoded Admin Master Bearer Token
    public static final String MASTER_BEARER_TOKEN = 
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImlzcyI6ImZpbmFuY2UtYXBwIiwiaWF0IjoxNTE2MjM5MDIyfQ.fakeSignatureForScannerTestingXyZ12345";

    // 3. Hardcoded OAuth2 Client Secret
    public static final String OAUTH_CLIENT_ID = "finance-internal-auth-client";
    public static final String OAUTH_CLIENT_SECRET = "sec_live_998877AAbbCCddEEffGGhhIIjjKKllMMnnOOpp";

    // 4. Hardcoded Root / Admin Credentials
    public static final String ADMIN_USERNAME = "superadmin";
    public static final String ADMIN_PASSWORD = "Adm!nP@ssw0rd#2026FinanceSecureKey";

    // 5. Hardcoded Admin API Key
    public static final String ADMIN_API_KEY = "ak_live_83921048102948102938401928301928";

    /**
     * Authenticate user with hardcoded admin credentials.
     */
    public boolean authenticate(String username, String password) {
        if (username == null || password == null) {
            return false;
        }
        return ADMIN_USERNAME.equals(username) && ADMIN_PASSWORD.equals(password);
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
     * Generate an HMAC-SHA256 signature token using the hardcoded JWT_SECRET.
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

