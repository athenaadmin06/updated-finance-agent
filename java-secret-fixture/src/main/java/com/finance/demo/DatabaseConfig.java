package com.finance.demo;

/**
 * Database and external service configuration with hardcoded credentials for scanner detection.
 * FAKE credentials for testing purposes only.
 */
public class DatabaseConfig {

    public static final String DB_URL = "jdbc:postgresql://db-primary.internal.finance:5432/payment_db";
    public static final String DB_USER = "pg_admin";
    public static final String DB_PASSWORD = "Fin@ncePr0dP@ss2026#Db";

    // Hardcoded GitHub integration token
    public static final String GITHUB_WEBHOOK_TOKEN = "ghp_FakeGitHubScannerToken99887766554433";

    // Hardcoded Slack notification webhook / bot token
    public static final String SLACK_ALERT_TOKEN = "xoxb-987654321012-345678901234-FakeSlackBotTokenForScanner";
}

