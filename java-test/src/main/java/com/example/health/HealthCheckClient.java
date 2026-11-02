package com.example.health;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

/**
 * Client API for invoking and verifying the Java Health Check API.
 * Uses standard java.net.http.HttpClient (JDK 11+).
 */
public class HealthCheckClient {

    private final HttpClient httpClient;
    private final Duration timeout;

    public HealthCheckClient() {
        this(Duration.ofSeconds(5));
    }

    public HealthCheckClient(Duration timeout) {
        this.timeout = timeout;
        this.httpClient = HttpClient.newBuilder()
                .connectTimeout(timeout)
                .build();
    }

    public static class HealthResponse {
        private final int statusCode;
        private final String body;

        public HealthResponse(int statusCode, String body) {
            this.statusCode = statusCode;
            this.body = body;
        }

        public int getStatusCode() {
            return statusCode;
        }

        public String getBody() {
            return body;
        }

        public boolean isHealthy() {
            return statusCode == 200 && body != null && body.contains("\"status\":\"UP\"");
        }

        @Override
        public String toString() {
            return String.format("HealthResponse[statusCode=%d, healthy=%s, body=%s]", statusCode, isHealthy(), body);
        }
    }

    /**
     * Executes health check with an auth token using standard Bearer authorization header.
     *
     * @param endpointUrl URL of the health check endpoint (e.g. "http://localhost:8080/health")
     * @param authToken   The authentication token (or null to omit)
     * @return HealthResponse containing status code and response payload
     */
    public HealthResponse checkHealth(String endpointUrl, String authToken) throws IOException, InterruptedException {
        HttpRequest.Builder builder = HttpRequest.newBuilder()
                .uri(URI.create(endpointUrl))
                .timeout(timeout)
                .GET();

        if (authToken != null && !authToken.isBlank()) {
            builder.header("Authorization", "Bearer " + authToken.trim());
        }

        HttpRequest request = builder.build();
        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());

        return new HealthResponse(response.statusCode(), response.body());
    }

    /**
     * Automated verification suite demonstrating and testing the Health Check API.
     */
    public static void main(String[] args) {
        System.out.println("==================================================");
        System.out.println(" Java Health Check API - Verification Suite");
        System.out.println("==================================================");

        int port = HealthCheckServer.resolvePort();
        if (args.length > 0) {
            try {
                port = Integer.parseInt(args[0]);
            } catch (NumberFormatException ignored) {}
        }

        String validToken = HealthCheckServer.resolveAuthToken();
        String healthUrl = "http://localhost:" + port + "/health";

        HealthCheckServer embeddedServer = null;
        boolean startedEmbedded = false;

        HealthCheckClient client = new HealthCheckClient();

        try {
            // Check if server is already running
            try {
                client.checkHealth(healthUrl, null);
                System.out.println("Connected to running server at: " + healthUrl + "\n");
            } catch (Exception notRunning) {
                System.out.println("No running server found on port " + port + ". Starting embedded server...");
                embeddedServer = new HealthCheckServer(port, validToken);
                embeddedServer.start();
                startedEmbedded = true;
                System.out.println("Embedded server started at: " + healthUrl + "\n");
            }

            boolean allPassed = true;

            // [Test 1] Missing Auth Token -> Expect 401 Unauthorized
            System.out.println("[Test 1] GET /health without Auth Token:");
            HealthResponse resp1 = client.checkHealth(healthUrl, null);
            boolean pass1 = (resp1.getStatusCode() == 401 && resp1.getBody().contains("Unauthorized"));
            System.out.printf("  -> Status: %d | Body: %s%n", resp1.getStatusCode(), resp1.getBody());
            System.out.println("  -> Result: " + (pass1 ? "PASSED (401 Unauthorized)" : "FAILED"));
            if (!pass1) allPassed = false;

            // [Test 2] Invalid Auth Token -> Expect 401 Unauthorized
            System.out.println("\n[Test 2] GET /health with Invalid Auth Token:");
            HealthResponse resp2 = client.checkHealth(healthUrl, "wrong-invalid-token");
            boolean pass2 = (resp2.getStatusCode() == 401 && resp2.getBody().contains("Unauthorized"));
            System.out.printf("  -> Status: %d | Body: %s%n", resp2.getStatusCode(), resp2.getBody());
            System.out.println("  -> Result: " + (pass2 ? "PASSED (401 Unauthorized)" : "FAILED"));
            if (!pass2) allPassed = false;

            // [Test 3] Valid Auth Token -> Expect 200 OK and status UP
            System.out.println("\n[Test 3] GET /health with Valid Auth Token:");
            HealthResponse resp3 = client.checkHealth(healthUrl, validToken);
            boolean pass3 = (resp3.getStatusCode() == 200 && resp3.isHealthy());
            System.out.printf("  -> Status: %d | Body: %s%n", resp3.getStatusCode(), resp3.getBody());
            System.out.println("  -> Result: " + (pass3 ? "PASSED (200 OK & status UP)" : "FAILED"));
            if (!pass3) allPassed = false;

            System.out.println("\n==================================================");
            if (allPassed) {
                System.out.println(" [SUCCESS] Health Check API verified successfully!");
            } else {
                System.err.println(" [FAILURE] Health Check API verification failed!");
                System.exit(1);
            }
            System.out.println("==================================================");

        } catch (Exception e) {
            System.err.println("Error executing health check client: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        } finally {
            if (startedEmbedded && embeddedServer != null) {
                embeddedServer.stop();
            }
        }
    }
}

