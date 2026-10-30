# dotnet-secret-fixture

Test fixture for secret-scanning tools (GitHub Advanced Security / Push Protection, GitGuardian, TruffleHog, Gitleaks) built with **.NET 9 / ASP.NET Core Minimal APIs**.

**Every credential in this directory is FAKE and intended solely for scanner testing.**
These are synthetic keys patterned after standard provider secret formats. None of them are valid credentials.

## Structure

| File | Purpose |
|------|---------|
| `Program.cs` | **HTTP Health Check API** requiring hardcoded bearer token (`sec_dotnet_health_token_8a7b6c5d4e3f2a1b0c9d`), plus automated test suite |
| `AuthService.cs` | Auth Service with hardcoded HMAC-SHA256 JWT secret, bearer token, OAuth secret, admin credentials, API key |
| `PaymentService.cs` | Service with hardcoded Stripe API secret key and AWS credentials |
| `DatabaseConfig.cs` | Class with hardcoded SQL Server connection string (SA password), Redis password, GitHub token, and Slack token |
| `SafeCredentialLoader.cs` | **Decoy**: Compliant credential resolution using environment variables (`Environment.GetEnvironmentVariable`) |
| `appsettings.json` | ASP.NET Core configuration file containing hardcoded connection strings and keys |
| `FinanceApi.csproj` | .NET 9 ASP.NET Core project file |
| `run.ps1` / `run.bat` | One-click automated self-test runner |
| `run-server.ps1` / `run-server.bat` | Script to run the interactive HTTP API server on port 5000 |

## How to Test

### Option 1: Run the Automated Self-Test (Fastest)

Runs the .NET self-test suite (validating admin login, cryptographic HMAC signing, and the HTTP Health Check API):

```powershell
& ".\run.ps1"
```

*Or directly via the .NET CLI:*
```powershell
dotnet run --project FinanceApi.csproj -- --test
```

### Option 2: Run the Server & Test Interactively with curl

1. Start the HTTP server on port 5000:
   ```powershell
   & ".\run-server.ps1"
   ```

2. In another terminal window, send test requests:

   **Without Token (Returns `401 Unauthorized`):**
   ```bash
   curl -i http://localhost:5000/api/health
   ```

   **With Invalid Token (Returns `401 Unauthorized`):**
   ```bash
   curl -i http://localhost:5000/api/health -H "Authorization: Bearer wrong_token"
   ```

   **With Hardcoded Token (Returns `200 OK`):**
   ```bash
   curl -i http://localhost:5000/api/health -H "Authorization: Bearer sec_dotnet_health_token_8a7b6c5d4e3f2a1b0c9d"
   ```

   *PowerShell alternative:*
   ```powershell
   Invoke-RestMethod -Uri "http://localhost:5000/api/health" -Headers @{ Authorization = "Bearer sec_dotnet_health_token_8a7b6c5d4e3f2a1b0c9d" }
   ```

### Option 3: Test Secret Scanners

To verify if your scanner flags the hardcoded .NET credentials and `appsettings.json`:

- **Gitleaks**:
  ```powershell
  gitleaks detect --source ./dotnet-secret-fixture -v
  ```
- **TruffleHog**:
  ```powershell
  trufflehog filesystem ./dotnet-secret-fixture
  ```
- **GitHub Push Protection**:
  ```powershell
  git add dotnet-secret-fixture/
  git commit -m "test: add dotnet secret fixture and health check api"
  git push origin main
  ```

