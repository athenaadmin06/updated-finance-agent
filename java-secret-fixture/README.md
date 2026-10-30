# java-secret-fixture

Test fixture for secret-scanning tools (GitHub Push Protection / Advanced Security, GitGuardian, TruffleHog, Gitleaks).

**Every credential in this directory is FAKE and intended solely for testing.**
These are synthetic keys patterned after standard provider secret formats. None of them are valid credentials.

## Structure

| File | Purpose |
|------|---------|
| `src/main/java/com/finance/demo/HealthCheckServer.java` | **HTTP Health Check API** requiring hardcoded bearer token (`sec_health_check_token_9f8d7c6b5a4e3d2c1b0a`) |
| `src/main/java/com/finance/demo/AuthService.java` | Auth Service with hardcoded HMAC JWT secret, master token, OAuth secret, admin credentials |
| `src/main/java/com/finance/demo/PaymentService.java` | Java service with hardcoded Stripe API secret key and AWS credentials |
| `src/main/java/com/finance/demo/DatabaseConfig.java` | Java configuration with hardcoded database password and API token |
| `src/main/java/com/finance/demo/SafeCredentialLoader.java` | **Decoy**: Compliant credential resolution using environment variables |
| `src/main/java/com/finance/demo/Application.java` | Automated test runner covering all services & the Health Check API |
| `run-server.ps1` / `run-server.bat` | Script to start the Health Check HTTP server on port 8080 |
| `run.ps1` / `run.bat` | One-click automated test runner |

## How to Test

### Option 1: Run the Automated Self-Test
Runs the server, fires test HTTP requests (no-auth, wrong-token, correct-token), and prints results:

```powershell
& ".\run.ps1"
```

### Option 2: Run the Server & Test Interactively with curl

1. Start the server (runs on port 8080):
   ```powershell
   & ".\run-server.ps1"
   ```

2. In another terminal, test with `curl`:
   ```bash
   # Test 1: Without token (Returns 401 Unauthorized)
   curl -i http://localhost:8080/api/health

   # Test 2: With incorrect token (Returns 401 Unauthorized)
   curl -i http://localhost:8080/api/health -H "Authorization: Bearer wrong_token"

   # Test 3: With hardcoded token (Returns 200 OK)
   curl -i http://localhost:8080/api/health -H "Authorization: Bearer sec_health_check_token_9f8d7c6b5a4e3d2c1b0a"
   ```
