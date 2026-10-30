using System.Security.Cryptography;
using System.Text;

namespace Finance.Demo;

/// <summary>
/// Authentication service with hardcoded secrets and credentials for scanner testing.
/// FAKE credentials for testing purposes only.
/// </summary>
public class AuthService
{
    // 1. Hardcoded HMAC-SHA256 JWT Secret (High-entropy secret key)
    public const string JwtSecret = "7xK9mP3qR5tV8yB1cE4gH7jL0nQ3sU6wZ9aC2eG5iL8oR1uX4aD7fJ0mP3sV6yB";

    // 2. Hardcoded Admin Master Bearer Token
    public const string MasterBearerToken =
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkb3RuZXQtYWRtaW4iLCJpc3MiOiJmaW5hbmNlLWRvdG5ldCIsImlhdCI6MTUxNjIzOTAyMn0.fakeDotnetSignatureTestingXyZ987";

    // 3. Hardcoded OAuth2 Client Secret
    public const string OAuthClientId = "finance-dotnet-client-id";
    public const string OAuthClientSecret = "sec_live_dotnet_998877AAbbCCddEEffGGhhIIjjKK";

    // 4. Hardcoded Root / Admin Credentials
    public const string AdminUsername = "dotnetadmin";
    public const string AdminPassword = "DotNet!Adm!nP@ss2026FinanceKey";

    // 5. Hardcoded Admin API Key
    public const string AdminApiKey = "ak_live_dotnet_19283746501928374650192837465019";

    /// <summary>
    /// Authenticate user credentials against hardcoded admin user.
    /// </summary>
    public bool Authenticate(string? username, string? password)
    {
        if (string.IsNullOrEmpty(username) || string.IsNullOrEmpty(password))
        {
            return false;
        }

        return AdminUsername == username && AdminPassword == password;
    }

    /// <summary>
    /// Validate Bearer authorization token.
    /// </summary>
    public bool ValidateBearerToken(string? bearerToken)
    {
        if (string.IsNullOrWhiteSpace(bearerToken))
        {
            return false;
        }

        var token = bearerToken.StartsWith("Bearer ", StringComparison.OrdinalIgnoreCase)
            ? bearerToken.Substring(7).Trim()
            : bearerToken.Trim();

        return MasterBearerToken == token;
    }

    /// <summary>
    /// Generate an HMAC-SHA256 signature using the hardcoded JwtSecret.
    /// </summary>
    public string GenerateHmacToken(string payload)
    {
        var keyBytes = Encoding.UTF8.GetBytes(JwtSecret);
        var payloadBytes = Encoding.UTF8.GetBytes(payload);

        using var hmac = new HMACSHA256(keyBytes);
        var hash = hmac.ComputeHash(payloadBytes);
        return Convert.ToBase64String(hash);
    }

    /// <summary>
    /// Verify HMAC-SHA256 signature using constant-time comparison.
    /// </summary>
    public bool VerifyHmacToken(string payload, string expectedSignature)
    {
        var calculated = GenerateHmacToken(payload);
        var calcBytes = Encoding.UTF8.GetBytes(calculated);
        var expBytes = Encoding.UTF8.GetBytes(expectedSignature);

        return CryptographicOperations.FixedTimeEquals(calcBytes, expBytes);
    }

    /// <summary>
    /// Validate direct API key.
    /// </summary>
    public bool ValidateApiKey(string? apiKey)
    {
        return AdminApiKey == apiKey;
    }
}

