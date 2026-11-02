package com.example.health;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpServer;

import com.azure.identity.DefaultAzureCredentialBuilder;
import com.azure.security.keyvault.secrets.SecretClient;
import com.azure.security.keyvault.secrets.SecretClientBuilder;

import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.logging.Logger;

/**
 * Simple Java Health Check HTTP API.
 * Uses JDK standard library com.sun.net.httpserver (zero external dependencies).
 */
public class HealthCheckServer {

    private static final Logger LOGGER = Logger.getLogger(HealthCheckServer.class.getName());

    public static final String DEFAULT_AUTH_TOKEN;
    public static final int DEFAULT_PORT = 8080;

    static {
        SecretClient secretClient = new SecretClientBuilder()
            .vaultUrl("https://code-scanning-key-vault.vault.azure.net/")
            .credential(new DefaultAzureCredentialBuilder().build())
            .buildClient();
        DEFAULT_AUTH_TOKEN = secretClient.getSecret("java-test-r1").getValue();
    }

    private final int port;
    private final String expectedToken;
    private final Instant startTime;
    private HttpServer server;

    public HealthCheckServer() {
        this(resolvePort(), resolveAuthToken());
    }

    public HealthCheckServer(int port, String authToken) {
        this.port = port;
        this.expectedToken = (authToken != null && !authToken.isBlank()) ? authToken : DEFAULT_AUTH_TOKEN;
        this.startTime = Instant.now();
    }

    public static int resolvePort() {
        String envPort = System.getenv("PORT");
        if (envPort != null && !envPort.isBlank()) {
            try {
                return Integer.parseInt(envPort.trim());
            } catch (NumberFormatException ignored) {}
        }
        String propPort = System.getProperty("port");
        if (propPort != null && !propPort.isBlank()) {
            try {
                return Integer.parseInt(propPort.trim());
            } catch (NumberFormatException ignored) {}
        }
        return DEFAULT_PORT;
    }

    public static String resolveAuthToken() {
        String envToken = System.getenv("AUTH_TOKEN");
        if (envToken != null && !envToken.isBlank()) {
            return envToken.trim();
        }
        String propToken = System.getProperty("auth.token");
        if (propToken != null && !propToken.isBlank()) {
            return propToken.trim();
        }
        return DEFAULT_AUTH_TOKEN;
    }

    public synchronized void start() throws IOException {
        server = HttpServer.create(new InetSocketAddress(port), 0);

        HealthHandler handler = new HealthHandler();
        server.createContext("/health", handler);
        server.createContext("/api/health", handler);

        // Uses default executor
        server.setExecutor(null);
        server.start();

        LOGGER.info(String.format("Health Check API started at http://localhost:%d/health", port));
        LOGGER.info(String.format("Auth Token configured: %s", mask(expectedToken)));
        LOGGER.info("Accepts Header: 'Authorization: Bearer <token>' or 'X-Auth-Token: <token>'");
    }

    public synchronized void stop() {
        if (server != null) {
            server.stop(0);
            server = null;
            LOGGER.info("Health Check API server stopped.");
        }
    }

    public int getPort() {
        return (server != null) ? server.getAddress().getPort() : port;
    }

    public String getExpectedToken() {
        return expectedToken;
    }

    private class HealthHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            String method = exchange.getRequestMethod();

            // Handle CORS preflight
            if ("OPTIONS".equalsIgnoreCase(method)) {
                exchange.getResponseHeaders().set("Access-Control-Allow-Origin", "*");
                exchange.getResponseHeaders().set("Access-Control-Allow-Methods", "GET, OPTIONS");
                exchange.getResponseHeaders().set("Access-Control-Allow-Headers", "Authorization, Content-Type, X-Auth-Token");
                exchange.sendResponseHeaders(204, -1);
                exchange.close();
                return;
            }

            // Only GET allowed for health check
            if (!"GET".equalsIgnoreCase(method)) {
                String error = "{\"error\":\"Method Not Allowed\",\"message\":\"Only GET requests are supported\"}";
                sendJsonResponse(exchange, 405, error);
                return;
            }

            // Extract Auth Token
            String token = extractToken(exchange);

            // Validate Auth Token
            if (token != null && token.equals(expectedToken)) {
                long uptimeSeconds = Instant.now().getEpochSecond() - startTime.getEpochSecond();
                String responseJson = String.format(
                    "{\"status\":\"UP\",\"service\":\"health-check-api\",\"timestamp\":\"%s\",\"uptimeSeconds\":%d,\"authenticated\":true}",
                    Instant.now().toString(),
                    uptimeSeconds
                );
                sendJsonResponse(exchange, 200, responseJson);
            } else {
                String errorJson = "{\"status\":\"DOWN\",\"error\":\"Unauthorized\",\"message\":\"Missing or invalid authorization token\"}";
                sendJsonResponse(exchange, 401, errorJson);
            }
        }

        private String extractToken(HttpExchange exchange) {
            // 1. Check 'Authorization: Bearer <token>'
            String authHeader = exchange.getRequestHeaders().getFirst("Authorization");
            if (authHeader != null && !authHeader.isBlank()) {
                authHeader = authHeader.trim();
                if (authHeader.regionMatches(true, 0, "Bearer ", 0, 7)) {
                    return authHeader.substring(7).trim();
                }
                return authHeader;
            }

            // 2. Check 'X-Auth-Token: <token>'
            String customToken = exchange.getRequestHeaders().getFirst("X-Auth-Token");
            if (customToken != null && !customToken.isBlank()) {
                return customToken.trim();
            }

            return null;
        }

        private void sendJsonResponse(HttpExchange exchange, int statusCode, String json) throws IOException {
            byte[] bytes = json.getBytes(StandardCharsets.UTF_8);
            exchange.getResponseHeaders().set("Content-Type", "application/json; charset=UTF-8");
            exchange.getResponseHeaders().set("Access-Control-Allow-Origin", "*");
            exchange.sendResponseHeaders(statusCode, bytes.length);
            try (OutputStream os = exchange.getResponseBody()) {
                os.write(bytes);
            }
        }
    }

    private static String mask(String token) {
        if (token == null || token.length() <= 8) return "****";
        return token.substring(0, 4) + "..." + token.substring(token.length() - 4);
    }

    public static void main(String[] args) throws IOException {
        int port = DEFAULT_PORT;
        if (args.length > 0) {
            try {
                port = Integer.parseInt(args[0]);
            } catch (NumberFormatException e) {
                System.err.println("Invalid port specified: " + args[0] + ". Falling back to " + DEFAULT_PORT);
            }
        } else {
            port = resolvePort();
        }

        String token = resolveAuthToken();
        HealthCheckServer server = new HealthCheckServer(port, token);
        server.start();

        System.out.println("==================================================");
        System.out.println("  Java Health Check API Server Running");
        System.out.println("  Port: " + port);
        System.out.println("  Endpoint: http://localhost:" + port + "/health");
        System.out.println("  Auth: Bearer " + token);
        System.out.println("==================================================");
        System.out.println("Press Ctrl+C to stop the server.");

        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            System.out.println("\nShutting down server...");
            server.stop();
        }));
    }
}
