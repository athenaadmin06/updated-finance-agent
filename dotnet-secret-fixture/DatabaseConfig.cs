namespace Finance.Demo;

/// <summary>
/// Database and external integration configuration with hardcoded credentials for scanner detection.
/// FAKE credentials for testing purposes only.
/// </summary>
public static class DatabaseConfig
{
    // Hardcoded SQL Server connection string with SA password
    public const string ConnectionString =
        "Server=sql-prod.internal.finance,1433;Database=FinanceDb;User Id=sa;Password=Fin@nceAdm!nP@ss2026#;TrustServerCertificate=True";

    // Hardcoded Redis Cache connection string with password
    public const string RedisConnection =
        "redis-prod.internal.finance:6379,password=Pr0dRed!sP@ssw0rd9988,ssl=False";

    // Hardcoded GitHub integration token
    public const string GitHubWebhookToken = "ghp_DotNetFakeGitHubScannerToken112233445566";

    // Hardcoded Slack notification webhook / bot token
    public const string SlackAlertToken = "xoxb-112233445566-778899001122-FakeSlackBotTokenForDotNet";
}

