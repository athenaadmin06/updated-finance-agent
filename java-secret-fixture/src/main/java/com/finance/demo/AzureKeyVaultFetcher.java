package com.finance.demo;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Azure Key Vault Secret Fetcher.
 * Allows toggling between:
 * 1. PURE_JAVA: Built-in JDK 21 (zero external dependencies, runs anywhere)
 * 2. AZURE_SDK: Official Azure SDK (DefaultAzureCredential + SecretClient)
 */
public class AzureKeyVaultFetcher {

    public enum FetchMode {
        PURE_JAVA,  // Standard JDK 21 HttpClient (Zero external JAR dependencies)
        AZURE_SDK   // Official Azure SDK (com.azure:azure-security-keyvault-secrets + azure-identity)
    }

    // =========================================================================
    // DEVELOPER TOGGLE: Change this variable to switch between modes!
    // =========================================================================
    public static final FetchMode ACTIVE_MODE = FetchMode.PURE_JAVA;

    public static final String DEFAULT_VAULT_URL = "https://code-scanning-key-vault.vault.azure.net/";
    public static final String DEFAULT_SECRET_NAME = "code-scan-api-key";

    public static void main(String[] args) {
        System.out.println("==================================================");
        System.out.println(" Azure Key Vault - Secret Fetcher");
        System.out.println(" Active Fetch Mode: " + ACTIVE_MODE);
        System.out.println("==================================================");

        String vaultUrl = System.getenv("KEY_VAULT_URL");
        if (vaultUrl == null || vaultUrl.isBlank()) {
            vaultUrl = DEFAULT_VAULT_URL;
        }

        String secretName = System.getenv("SECRET_NAME");
        if (secretName == null || secretName.isBlank()) {
            secretName = args.length > 0 ? args[0] : DEFAULT_SECRET_NAME;
        }

        if (!vaultUrl.endsWith("/")) {
            vaultUrl += "/";
        }

        System.out.println("Key Vault URL: " + vaultUrl);
        System.out.println("Secret Name:   " + secretName);

        try {
            String secretValue;

            if (ACTIVE_MODE == FetchMode.AZURE_SDK) {
                System.out.println("\n[Mode: AZURE_SDK] Fetching using Azure SDK (DefaultAzureCredential)...");
                secretValue = fetchViaAzureSdk(vaultUrl, secretName);
            } else {
                System.out.println("\n[Mode: PURE_JAVA] Fetching using standard JDK HttpClient & Azure session...");
                secretValue = fetchViaPureJava(vaultUrl, secretName);
            }

            System.out.println("\n==================================================");
            System.out.println(" [SUCCESS] Secret retrieved successfully!");
            System.out.println(" Mode Used:    " + ACTIVE_MODE);
            System.out.println(" Secret Name:  " + secretName);
            System.out.println(" Secret Value: " + secretValue);
            System.out.println("==================================================");

        } catch (Exception e) {
            System.err.println("\n[FAILED] Error fetching secret: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }
    }

    // =========================================================================
    // METHOD 1: PURE JAVA (Zero External Dependencies)
    // =========================================================================
    /**
     * Pure Java implementation using standard JDK 21 java.net.http.HttpClient.
     * Obtains access token via active Azure CLI session (no external JARs needed).
     */
    public static String fetchViaPureJava(String vaultUrl, String secretName) throws Exception {
        // 1. Acquire Azure access token
        String accessToken = getAzureCliToken();

        // 2. Query Azure Key Vault REST API
        String endpoint = vaultUrl + "secrets/" + secretName + "?api-version=7.4";
        HttpClient client = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(10))
                .build();

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(endpoint))
                .header("Authorization", "Bearer " + accessToken)
                .header("Accept", "application/json")
                .timeout(Duration.ofSeconds(15))
                .GET()
                .build();

        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());

        if (response.statusCode() == 200) {
            Pattern pattern = Pattern.compile("\"value\"\\s*:\\s*\"([^\"]+)\"");
            Matcher matcher = pattern.matcher(response.body());
            if (matcher.find()) {
                return matcher.group(1);
            }
            return response.body();
        } else {
            throw new RuntimeException("HTTP " + response.statusCode() + " from Key Vault: " + response.body());
        }
    }

    // =========================================================================
    // METHOD 2: OFFICIAL AZURE SDK (DefaultAzureCredential + SecretClient)
    // =========================================================================
    /**
     * Official Azure SDK implementation.
     * Equivalent to:
     *   SecretClient client = new SecretClientBuilder()
     *       .vaultUrl(vaultUrl)
     *       .credential(new DefaultAzureCredentialBuilder().build())
     *       .buildClient();
     *   return client.getSecret(secretName).getValue();
     *
     * (Dynamically loaded so the class compiles cleanly even if SDK JARs are not yet in classpath)
     */
    public static String fetchViaAzureSdk(String vaultUrl, String secretName) throws Exception {
        try {
            // Build DefaultAzureCredential
            Class<?> credBuilderClass = Class.forName("com.azure.identity.DefaultAzureCredentialBuilder");
            Object credBuilder = credBuilderClass.getDeclaredConstructor().newInstance();
            Object credential = credBuilderClass.getMethod("build").invoke(credBuilder);

            // Build SecretClient
            Class<?> clientBuilderClass = Class.forName("com.azure.security.keyvault.secrets.SecretClientBuilder");
            Object clientBuilder = clientBuilderClass.getDeclaredConstructor().newInstance();
            clientBuilderClass.getMethod("vaultUrl", String.class).invoke(clientBuilder, vaultUrl);

            Class<?> tokenCredClass = Class.forName("com.azure.core.credential.TokenCredential");
            clientBuilderClass.getMethod("credential", tokenCredClass).invoke(clientBuilder, credential);
            Object secretClient = clientBuilderClass.getMethod("buildClient").invoke(clientBuilder);

            // Fetch secret value
            Object keyVaultSecret = secretClient.getClass().getMethod("getSecret", String.class).invoke(secretClient, secretName);
            return (String) keyVaultSecret.getClass().getMethod("getValue").invoke(keyVaultSecret);

        } catch (ClassNotFoundException e) {
            throw new IllegalStateException(
                "Azure SDK classes not found on classpath.\n" +
                "To use FetchMode.AZURE_SDK, add 'azure-security-keyvault-secrets' and 'azure-identity' to pom.xml,\n" +
                "or switch ACTIVE_MODE to FetchMode.PURE_JAVA.", e
            );
        }
    }

    /**
     * Resolves Azure OAuth2 token via local Azure session or environment.
     */
    private static String getAzureCliToken() throws Exception {
        String envToken = System.getenv("AZURE_BEARER_TOKEN");
        if (envToken != null && !envToken.isBlank()) {
            return envToken.trim();
        }

        ProcessBuilder pb = new ProcessBuilder(
                "cmd.exe", "/c", "az account get-access-token --resource https://vault.azure.net --query accessToken -o tsv"
        );
        pb.redirectErrorStream(true);
        Process process = pb.start();

        StringBuilder output = new StringBuilder();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream(), StandardCharsets.UTF_8))) {
            String line;
            while ((line = reader.readLine()) != null) {
                output.append(line.trim());
            }
        }

        int exitCode = process.waitFor();
        if (exitCode != 0 || output.toString().trim().isEmpty()) {
            throw new RuntimeException("Failed to acquire Azure access token. az CLI output: " + output);
        }

        return output.toString().trim();
    }
}
