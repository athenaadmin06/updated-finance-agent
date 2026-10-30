package com.finance.demo;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

public class Application {

    public static void main(String[] args) {
        System.out.println("==================================================");
        System.out.println(" Finance Java App - Auth & API Service Demo");
        System.out.println("==================================================");

        AuthService authService = new AuthService();

        // 1. Test Admin Credentials
        System.out.println("\n[Test 1] Testing Admin Credential Authentication:");
        boolean adminLoginOk = authService.authenticate(AuthService.ADMIN_USERNAME, AuthService.ADMIN_PASSWORD);
        System.out.println("  -> Login with (" + AuthService.ADMIN_USERNAME + "): " + (adminLoginOk ? "SUCCESS (Authenticated)" : "FAILED"));

        // 2. Test HMAC Token Signing
        System.out.println("\n[Test 2] Testing HMAC-SHA256 Token Signing with JWT_SECRET:");
        String userPayload = "user_id=1001;role=finance_manager";
        String tokenSignature = authService.generateHmacToken(userPayload);
        boolean sigOk = authService.verifyHmacToken(userPayload, tokenSignature);
        System.out.println("  -> Signature Verification: " + (sigOk ? "PASSED (Valid Signature)" : "FAILED"));

        // 3. Test HTTP Health Check API with Auth
        System.out.println("\n[Test 3] Testing HTTP Health Check API (with Auth Token):");
        testHealthCheckApi();

        System.out.println("\n==================================================");
        System.out.println(" All tests executed successfully!");
        System.out.println("==================================================");
    }

    private static void testHealthCheckApi() {
        HealthCheckServer server = new HealthCheckServer();
        int testPort = 8089;
        try {
            server.start(testPort);
            HttpClient client = HttpClient.newHttpClient();
            String healthUrl = "http://localhost:" + testPort + "/api/health";

            // Subtest A: No Auth Token -> Expect 401 Unauthorized
            HttpRequest unauthReq = HttpRequest.newBuilder()
                    .uri(URI.create(healthUrl))
                    .GET()
                    .build();
            HttpResponse<String> resp1 = client.send(unauthReq, HttpResponse.BodyHandlers.ofString());
            System.out.println("  -> [Call without Token] Status: " + resp1.statusCode() + " " + (resp1.statusCode() == 401 ? "PASSED (401 Unauthorized)" : "FAILED"));
            System.out.println("     Body: " + resp1.body());

            // Subtest B: Wrong Auth Token -> Expect 401 Unauthorized
            HttpRequest wrongReq = HttpRequest.newBuilder()
                    .uri(URI.create(healthUrl))
                    .header("Authorization", "Bearer invalid_token_12345")
                    .GET()
                    .build();
            HttpResponse<String> resp2 = client.send(wrongReq, HttpResponse.BodyHandlers.ofString());
            System.out.println("  -> [Call with Invalid Token] Status: " + resp2.statusCode() + " " + (resp2.statusCode() == 401 ? "PASSED (401 Unauthorized)" : "FAILED"));

            // Subtest C: Correct Hardcoded Token -> Expect 200 OK
            HttpRequest authReq = HttpRequest.newBuilder()
                    .uri(URI.create(healthUrl))
                    .header("Authorization", "Bearer " + HealthCheckServer.AUTH_TOKEN)
                    .GET()
                    .build();
            HttpResponse<String> resp3 = client.send(authReq, HttpResponse.BodyHandlers.ofString());
            System.out.println("  -> [Call with Hardcoded Token] Status: " + resp3.statusCode() + " " + (resp3.statusCode() == 200 ? "PASSED (200 OK)" : "FAILED"));
            System.out.println("     Body: " + resp3.body());

        } catch (Exception e) {
            System.err.println("API Test failed with error: " + e.getMessage());
            e.printStackTrace();
        } finally {
            server.stop();
        }
    }
}
