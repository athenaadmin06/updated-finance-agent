using System.Net.Http.Headers;
using Finance.Demo;

namespace Finance.Demo;

public class Program
{
    // Hardcoded Authentication Token for Health Check API
    public const string HealthAuthToken = "sec_dotnet_health_token_8a7b6c5d4e3f2a1b0c9d";

    public static async Task Main(string[] args)
    {
        // If run with --test, execute automated test suite
        if (args.Contains("--test") || args.Contains("test"))
        {
            await RunSelfTestsAsync();
            return;
        }

        var app = CreateApp(args);
        Console.WriteLine($"Health Check API running.");
        Console.WriteLine($"Hardcoded Token: {HealthAuthToken}");
        Console.WriteLine($"Endpoints: http://localhost:5000/api/health or http://localhost:5000/health");
        await app.RunAsync();
    }

    public static WebApplication CreateApp(string[] args, string? url = null)
    {
        var builder = WebApplication.CreateBuilder(args);
        if (url != null)
        {
            builder.WebHost.UseUrls(url);
        }

        var app = builder.Build();

        // Health check endpoint requiring authentication
        Delegate healthHandler = (HttpContext context) =>
        {
            string? token = null;

            // Check Authorization header (Bearer <token>)
            if (context.Request.Headers.TryGetValue("Authorization", out var authHeaders))
            {
                var authHeader = authHeaders.ToString();
                if (authHeader.StartsWith("Bearer ", StringComparison.OrdinalIgnoreCase))
                {
                    token = authHeader.Substring(7).Trim();
                }
                else
                {
                    token = authHeader.Trim();
                }
            }
            // Check X-Auth-Token header
            else if (context.Request.Headers.TryGetValue("X-Auth-Token", out var customHeaders))
            {
                token = customHeaders.ToString().Trim();
            }

            // Authenticate against hardcoded HealthAuthToken
            if (!string.IsNullOrEmpty(token) && token == HealthAuthToken)
            {
                return Results.Ok(new
                {
                    status = "UP",
                    timestamp = DateTime.UtcNow.ToString("o"),
                    service = "finance-dotnet-agent",
                    authenticated = true
                });
            }

            return Results.Json(new
            {
                error = "Unauthorized",
                message = "Missing or invalid authentication token"
            }, statusCode: 401);
        };

        app.MapGet("/api/health", healthHandler);
        app.MapGet("/health", healthHandler);

        return app;
    }

    private static async Task RunSelfTestsAsync()
    {
        Console.WriteLine("==================================================");
        Console.WriteLine(" .NET Finance App - Auth & API Service Demo");
        Console.WriteLine("==================================================");

        var authService = new AuthService();

        // 1. Test Admin Credentials
        Console.WriteLine("\n[Test 1] Testing Admin Credential Authentication:");
        bool adminLoginOk = authService.Authenticate(AuthService.AdminUsername, AuthService.AdminPassword);
        Console.WriteLine($"  -> Login with ({AuthService.AdminUsername}): {(adminLoginOk ? "SUCCESS (Authenticated)" : "FAILED")}");

        bool badLoginOk = authService.Authenticate("dotnetadmin", "wrong_password");
        Console.WriteLine($"  -> Login with wrong password: {(!badLoginOk ? "PASSED (Rejected)" : "FAILED")}");

        // 2. Test Master Bearer Token
        Console.WriteLine("\n[Test 2] Testing Master Bearer Token Validation:");
        string sampleHeader = "Bearer " + AuthService.MasterBearerToken;
        bool tokenOk = authService.ValidateBearerToken(sampleHeader);
        Console.WriteLine($"  -> Validate Bearer Header: {(tokenOk ? "SUCCESS (Authorized)" : "FAILED")}");

        // 3. Test HMAC Token Signing with JwtSecret
        Console.WriteLine("\n[Test 3] Testing HMAC-SHA256 Token Signing with JwtSecret:");
        string userPayload = "user_id=2002;role=dotnet_lead";
        string tokenSignature = authService.GenerateHmacToken(userPayload);
        Console.WriteLine($"  -> Payload:   {userPayload}");
        Console.WriteLine($"  -> Signature: {tokenSignature}");
        bool sigOk = authService.VerifyHmacToken(userPayload, tokenSignature);
        Console.WriteLine($"  -> Signature Verification: {(sigOk ? "PASSED (Valid Signature)" : "FAILED")}");

        // 4. Test API Key Validation
        Console.WriteLine("\n[Test 4] Testing API Key Validation:");
        bool apiKeyOk = authService.ValidateApiKey(AuthService.AdminApiKey);
        Console.WriteLine($"  -> Validate API Key: {(apiKeyOk ? "SUCCESS (Matched)" : "FAILED")}");

        // 5. Test Payment Service
        Console.WriteLine("\n[Test 5] Testing Payment & AWS Storage Mock:");
        var paymentService = new PaymentService();
        paymentService.ProcessPayment("cust_dotnet_5511", 129.50m);
        paymentService.ArchiveReceipt("rcpt_dotnet_7722");

        // 6. Test HTTP Health Check API
        Console.WriteLine("\n[Test 6] Testing HTTP Health Check API (with Auth Token):");
        string testUrl = "http://localhost:5199";
        var app = CreateApp(Array.Empty<string>(), testUrl);
        var appTask = app.RunAsync();

        try
        {
            using var client = new HttpClient { BaseAddress = new Uri(testUrl) };
            
            // Subtest A: No Token -> Expect 401
            var resp1 = await client.GetAsync("/api/health");
            var body1 = await resp1.Content.ReadAsStringAsync();
            Console.WriteLine($"  -> [Call without Token] Status: {(int)resp1.StatusCode} {(resp1.StatusCode == System.Net.HttpStatusCode.Unauthorized ? "PASSED (401 Unauthorized)" : "FAILED")}");
            Console.WriteLine($"     Body: {body1}");

            // Subtest B: Wrong Token -> Expect 401
            using var wrongReq = new HttpRequestMessage(HttpMethod.Get, "/api/health");
            wrongReq.Headers.Authorization = new AuthenticationHeaderValue("Bearer", "invalid_token_999");
            var resp2 = await client.SendAsync(wrongReq);
            Console.WriteLine($"  -> [Call with Invalid Token] Status: {(int)resp2.StatusCode} {(resp2.StatusCode == System.Net.HttpStatusCode.Unauthorized ? "PASSED (401 Unauthorized)" : "FAILED")}");

            // Subtest C: Hardcoded Token -> Expect 200 OK
            using var authReq = new HttpRequestMessage(HttpMethod.Get, "/api/health");
            authReq.Headers.Authorization = new AuthenticationHeaderValue("Bearer", HealthAuthToken);
            var resp3 = await client.SendAsync(authReq);
            var body3 = await resp3.Content.ReadAsStringAsync();
            Console.WriteLine($"  -> [Call with Hardcoded Token] Status: {(int)resp3.StatusCode} {(resp3.StatusCode == System.Net.HttpStatusCode.OK ? "PASSED (200 OK)" : "FAILED")}");
            Console.WriteLine($"     Body: {body3}");
        }
        finally
        {
            await app.StopAsync();
            await appTask;
        }

        Console.WriteLine("\n==================================================");
        Console.WriteLine(" All .NET tests executed successfully!");
        Console.WriteLine("==================================================");
    }
}

