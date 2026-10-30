package com.finance.demo;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpServer;

import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.time.Instant;

/**
 * Lightweight HTTP Health Check API requiring authentication.
 * Uses standard JDK com.sun.net.httpserver (zero external dependencies).
 */
public class HealthCheckServer {

    // Hardcoded Authentication Token for Scanner Testing
    public static final String AUTH_TOKEN = "sec_health_check_token_9f8d7c6b5a4e3d2c1b0a";
    public static final int DEFAULT_PORT = 8080;

    private HttpServer server;

    public void start(int port) throws IOException {
        server = HttpServer.create(new InetSocketAddress(port), 0);
        server.createContext("/api/health", new HealthCheckHandler());
        server.createContext("/health", new HealthCheckHandler());
        server.setExecutor(null); // default executor
        server.start();
        System.out.println("HealthCheckServer started at http://localhost:" + port + "/api/health");
        System.out.println("Required Header: Authorization: Bearer " + AUTH_TOKEN);
    }

    public void stop() {
        if (server != null) {
            server.stop(0);
            System.out.println("HealthCheckServer stopped.");
        }
    }

    public int getPort() {
        return server != null ? server.getAddress().getPort() : -1;
    }

    static class HealthCheckHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            if (!"GET".equalsIgnoreCase(exchange.getRequestMethod())) {
                sendResponse(exchange, 405, "{\"error\": \"Method Not Allowed\"}");
                return;
            }

            // Extract auth header (supports 'Authorization: Bearer <token>' or 'X-Auth-Token')
            String authHeader = exchange.getRequestHeaders().getFirst("Authorization");
            String customToken = exchange.getRequestHeaders().getFirst("X-Auth-Token");

            String token = null;
            if (authHeader != null && authHeader.startsWith("Bearer ")) {
                token = authHeader.substring(7).trim();
            } else if (authHeader != null) {
                token = authHeader.trim();
            } else if (customToken != null) {
                token = customToken.trim();
            }

            // Authenticate token against hardcoded AUTH_TOKEN
            if (AUTH_TOKEN.equals(token)) {
                String responseJson = String.format(
                    "{\"status\":\"UP\",\"timestamp\":\"%s\",\"service\":\"finance-agent\",\"authenticated\":true}",
                    Instant.now().toString()
                );
                sendResponse(exchange, 200, responseJson);
            } else {
                String errorJson = "{\"error\":\"Unauthorized\",\"message\":\"Missing or invalid authentication token\"}";
                sendResponse(exchange, 401, errorJson);
            }
        }

        private void sendResponse(HttpExchange exchange, int statusCode, String responseBody) throws IOException {
            byte[] bytes = responseBody.getBytes(StandardCharsets.UTF_8);
            exchange.getResponseHeaders().set("Content-Type", "application/json");
            exchange.sendResponseHeaders(statusCode, bytes.length);
            try (OutputStream os = exchange.getResponseBody()) {
                os.write(bytes);
            }
        }
    }

    public static void main(String[] args) throws IOException {
        int port = DEFAULT_PORT;
        if (args.length > 0) {
            try {
                port = Integer.parseInt(args[0]);
            } catch (NumberFormatException ignored) {}
        }

        HealthCheckServer server = new HealthCheckServer();
        server.start(port);
        System.out.println("Server is running. Press Ctrl+C to stop.");
    }
}

