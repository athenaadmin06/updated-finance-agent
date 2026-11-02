package com.finance.demo;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

/**
 * Health Check API Test and Verification Suite for Java.
 *
 * Can be run against an already running HealthCheckServer on port 8080,
 * or will automatically spin up an in-process HealthCheckServer if none is running.
 *
 * Usage:
 *   java -cp target-classes com.finance.demo.HealthCheckTest [optional-port]
 *   or:
 *   java src/main/java/com/finance/demo/HealthCheckTest.java
 */
public class HealthCheckTest {

    public static void main(String[] args) {
        System.out.println("==================================================");
        System.out.println(" Java Health Check API - Verification Suite");
        System.out.println("==================================================");

        // Read token from environment variable first (if remediated), fallback to HealthCheckServer.AUTH_TOKEN
        String envToken = System.getenv("AUTH_TOKEN");
        if (envToken == null || envToken.isBlank()) {
            envToken = System.getenv("HEALTH_AUTH_TOKEN");
        }
        String validToken = (envToken != null && !envToken.isBlank())
                ? envToken.trim()
                : HealthCheckServer.AUTH_TOKEN;

        int port = HealthCheckServer.DEFAULT_PORT;
        if (args.length > 0) {
            try {
                port = Integer.parseInt(args[0]);
            } catch (NumberFormatException ignored) {}
        }

        String baseUrl = "http://localhost:" + port;
        String healthUrl = baseUrl + "/api/health";

        HealthCheckServer server = null;
        boolean startedInternalServer = false;

        HttpClient client = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(3))
                .build();

        try {
            // Check if server is already running on target port
            boolean isRunning = false;
            try {
                HttpRequest ping = HttpRequest.newBuilder()
                        .uri(URI.create(healthUrl))
                        .timeout(Duration.ofSeconds(1))
                        .GET()
                        .build();
                client.send(ping, HttpResponse.BodyHandlers.discarding());
                isRunning = true;
                System.out.println("Target: Existing server detected at " + healthUrl + "\n");
            } catch (Exception notRunning) {
                System.out.println("No running server found on port " + port + ". Starting in-process HealthCheckServer...");
                server = new HealthCheckServer();
                server.start(port);
                startedInternalServer = true;
                System.out.println("Embedded HealthCheckServer started at " + healthUrl + "\n");
            }

            boolean allPassed = true;

            // [Test 1] Missing Token -> Expect 401 Unauthorized
            System.out.println("[Test 1] GET /api/health (No Auth Token):");
            HttpRequest req1 = HttpRequest.newBuilder()
                    .uri(URI.create(healthUrl))
                    .GET()
                    .build();
            HttpResponse<String> resp1 = client.send(req1, HttpResponse.BodyHandlers.ofString());
            boolean pass1 = resp1.statusCode() == 401 && resp1.body().contains("Unauthorized");
            System.out.printf("  -> Status: %d | Body: %s%n", resp1.statusCode(), resp1.body());
            System.out.println("  -> Result: " + (pass1 ? "PASSED (401 Unauthorized as expected)" : "FAILED"));
            if (!pass1) allPassed = false;

            // [Test 2] Invalid Token -> Expect 401 Unauthorized
            System.out.println("\n[Test 2] GET /api/health (Invalid Token 'Bearer wrong_token_12345'):");
            HttpRequest req2 = HttpRequest.newBuilder()
                    .uri(URI.create(healthUrl))
                    .header("Authorization", "Bearer wrong_token_12345")
                    .GET()
                    .build();
            HttpResponse<String> resp2 = client.send(req2, HttpResponse.BodyHandlers.ofString());
            boolean pass2 = resp2.statusCode() == 401 && resp2.body().contains("Unauthorized");
            System.out.printf("  -> Status: %d | Body: %s%n", resp2.statusCode(), resp2.body());
            System.out.println("  -> Result: " + (pass2 ? "PASSED (401 Unauthorized as expected)" : "FAILED"));
            if (!pass2) allPassed = false;

            // [Test 3] Valid Token -> Expect 200 OK
            System.out.println("\n[Test 3] GET /api/health (Valid Token 'Bearer " + mask(validToken) + "'):");
            HttpRequest req3 = HttpRequest.newBuilder()
                    .uri(URI.create(healthUrl))
                    .header("Authorization", "Bearer " + validToken)
                    .GET()
                    .build();
            HttpResponse<String> resp3 = client.send(req3, HttpResponse.BodyHandlers.ofString());
            boolean pass3 = resp3.statusCode() == 200 && resp3.body().contains("\"status\":\"UP\"");
            System.out.printf("  -> Status: %d | Body: %s%n", resp3.statusCode(), resp3.body());
            System.out.println("  -> Result: " + (pass3 ? "PASSED (200 OK & status UP)" : "FAILED"));
            if (!pass3) allPassed = false;

            System.out.println("\n==================================================");
            if (allPassed) {
                System.out.println(" [SUCCESS] Health Check API is WORKING FINE!");
                System.out.println(" All 3 health check test cases passed successfully.");
            } else {
                System.err.println(" [FAILURE] Health Check API test FAILED!");
                System.exit(1);
            }
            System.out.println("==================================================");

        } catch (Exception e) {
            System.err.println("\n[ERROR] Health check test execution error: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        } finally {
            if (startedInternalServer && server != null) {
                server.stop();
            }
        }
    }

    private static String mask(String token) {
        if (token == null || token.length() <= 8) return "****";
        return token.substring(0, 4) + "..." + token.substring(token.length() - 4);
    }
}
