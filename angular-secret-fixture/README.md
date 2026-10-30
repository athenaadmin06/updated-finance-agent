# angular-secret-fixture

Test fixture for secret-scanning tools (GitHub Advanced Security / Push Protection, GitGuardian, TruffleHog, Gitleaks) covering **Angular SSR (Server-Side Rendering) backend APIs and frontend environment leak patterns**.

**Every credential in this directory is FAKE and intended solely for testing.**
These are synthetic keys patterned after standard provider secret formats. None of them are valid credentials.

## Is It Possible to Have an API in Angular?

Yes! While traditional Angular is a pure client-side SPA in the browser, modern Angular architectures frequently include APIs through:
1. **Angular SSR (`@angular/ssr` / Angular Universal)**: Uses a Node.js/Express server (`server.ts` / `server.mjs`) to render Angular on the server and host BFF (Backend-for-Frontend) or health check APIs directly.
2. **Angular BFF / Mock API Server**: A lightweight Node server bundled with Angular during development or deployment.
3. **Frontend Secret Leaks**: A common mistake where developers accidentally embed private keys (Stripe secret keys, AWS credentials) into `src/environments/environment.prod.ts`, exposing them to browser clients and secret scanners.

## Structure

| File | Purpose |
|------|---------|
| `server.mjs` | **Angular SSR / Node API server** hosting `/api/health` requiring hardcoded token (`sec_angular_health_token_7d6c5b4a3e2f1a0b9c8d`), plus hardcoded SSR JWT and MongoDB secrets |
| `src/environments/environment.prod.ts` | **Frontend Secret Leaks**: Hardcoded Stripe secret key (`sk_live_...`), AWS keys (`AKIA...`), Google Maps key, Firebase key |
| `src/environments/environment.ts` | Development environment with test secrets |
| `src/app/services/auth.service.ts` | Angular service managing hardcoded bearer token |
| `src/app/services/health.service.ts` | Angular HTTP service calling `/api/health` |
| `src/app/interceptors/auth.interceptor.ts` | HTTP interceptor attaching Bearer token to requests |
| `src/app/services/safe-config.service.ts` | **Decoy**: Demonstrates safe runtime config loading from `/assets/config.json` |
| `test.mjs` | Automated test suite for `/api/health` |
| `run.ps1` / `run.bat` | One-click automated self-test runner |
| `run-server.ps1` / `run-server.bat` | Script to start the Angular API server on port 4200 |

## How to Test

### Option 1: Run the Automated Self-Test (Fastest)

Runs the automated API tests (validating missing token -> 401, invalid token -> 401, hardcoded token -> 200):

```powershell
& ".\run.ps1"
```

*Or with Node:*
```bash
node test.mjs
```

### Option 2: Run the Server & Test Interactively with curl

1. Start the server (runs on port 4200):
   ```powershell
   & ".\run-server.ps1"
   ```

2. In another terminal window, send test requests:

   **Without Token (Returns `401 Unauthorized`):**
   ```bash
   curl -i http://localhost:4200/api/health
   ```

   **With Invalid Token (Returns `401 Unauthorized`):**
   ```bash
   curl -i http://localhost:4200/api/health -H "Authorization: Bearer wrong_token"
   ```

   **With Hardcoded Token (Returns `200 OK`):**
   ```bash
   curl -i http://localhost:4200/api/health -H "Authorization: Bearer sec_angular_health_token_7d6c5b4a3e2f1a0b9c8d"
   ```

   *PowerShell alternative:*
   ```powershell
   Invoke-RestMethod -Uri "http://localhost:4200/api/health" -Headers @{ Authorization = "Bearer sec_angular_health_token_7d6c5b4a3e2f1a0b9c8d" }
   ```

### Option 3: Test Secret Scanners

To verify if your scanner flags the hardcoded Angular environment leaks and SSR server secrets:

- **Gitleaks**:
  ```powershell
  gitleaks detect --source ./angular-secret-fixture -v
  ```
- **TruffleHog**:
  ```powershell
  trufflehog filesystem ./angular-secret-fixture
  ```
- **GitHub Push Protection**:
  ```powershell
  git add angular-secret-fixture/
  git commit -m "test: add angular secret fixture and health check api"
  git push origin main
  ```

