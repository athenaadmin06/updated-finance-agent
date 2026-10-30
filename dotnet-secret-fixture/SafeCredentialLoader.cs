namespace Finance.Demo;

/// <summary>
/// Decoy class: demonstrates compliant credential retrieval via environment variables.
/// Secret scanners should NOT flag this class.
/// </summary>
public class SafeCredentialLoader
{
    public string GetStripeApiKey()
    {
        var key = Environment.GetEnvironmentVariable("STRIPE_API_KEY");
        if (string.IsNullOrWhiteSpace(key))
        {
            throw new InvalidOperationException("STRIPE_API_KEY environment variable is not configured");
        }
        return key;
    }

    public string GetAwsSecretKey()
    {
        var secret = Environment.GetEnvironmentVariable("AWS_SECRET_ACCESS_KEY");
        if (string.IsNullOrWhiteSpace(secret))
        {
            throw new InvalidOperationException("AWS_SECRET_ACCESS_KEY environment variable is not configured");
        }
        return secret;
    }

    public string GetDatabaseConnectionString()
    {
        var connStr = Environment.GetEnvironmentVariable("DATABASE_CONNECTION_STRING");
        if (string.IsNullOrWhiteSpace(connStr))
        {
            throw new InvalidOperationException("DATABASE_CONNECTION_STRING environment variable is not configured");
        }
        return connStr;
    }
}

