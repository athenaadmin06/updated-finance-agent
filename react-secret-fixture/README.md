# react-secret-fixture

Test fixture for secret-scanning tools (GitHub Advanced Security / Push Protection, GitGuardian, TruffleHog, Gitleaks) covering **React / Next.js backend API routes and client-side environment secret leaks**.

**Every credential in this directory is FAKE and intended solely for testing.**
These are synthetic keys patterned after standard provider secret formats. None of them are valid credentials.

## Is It Possible to Have an API in React?

Yes! Modern React apps handle APIs through:
1. **Full-stack React (Next.js / Remix / Astro)**: Next.js has built-in API Routes (`app/api/...` or `pages/api/...`) and Server Actions running on Node.js/Edge runtimes.
2. **React BFF (Backend-for-Frontend) / Node Proxy**: React SPAs are paired with a lightweight Node.js/Express server in the same repo to serve mock data, handle authentication, or proxy backend requests.
3. **The Common React Vulnerability (Environment Leaks)**: Developers frequently make the severe mistake of prefixing private keys with `REACT_APP_`, `VITE_`, or `NEXT_PUBLIC_` in `.env.production` (e.g. `REACT_APP_STRIPE_SECRET_KEY=sk_live_...`). These variables are bundled directly into the browser client JavaScript, making them public and triggering secret scanning alerts.

## Structure

| File | Purpose |
|------|---------|
| `server.mjs` | **React Next.js / Express style API server** hosting `/api/health` requiring hardcoded token (`sec_react_health_token_6e5d4c3b2a1f0e9d8c7b`) |
| `src/api/healthRoute.js` | Server route handler with hardcoded NextAuth and Supabase secrets |
| `.env.production` | **Frontend Secret Leaks**: Leaked Stripe secret key (`sk_live_...`), AWS keys (`AKIA...`), and OpenAI API key (`sk-proj-...`) |
| `.env` | Development environment with test secrets |
| `src/services/authService.js` | React client auth service managing master bearer token |
| `src/services/safeConfigService.js` | **Decoy**: Demonstrates safe runtime config loading from `/config.json` |
| `src/hooks/useHealthCheck.js` | React hook fetching `/api/health` with auth headers |
| `src/App.jsx` | React component consuming the health check hook |
| `test.mjs` | Automated test suite verifying missing, invalid, and valid auth scenarios |
| `run.ps1` / `run.bat` | One-click automated self-test runner |
| `run-server.ps1` / `run-server.bat` | Script to start the React API server on port 3000 |

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

1. Start the server (runs on port 3000):
   ```powershell
   & ".\run-server.ps1"
   ```

2. In another terminal window, send test requests:

   **Without Token (Returns `401 Unauthorized`):**
   ```bash
   curl -i http://localhost:3000/api/health
   ```

   **With Invalid Token (Returns `401 Unauthorized`):**
   ```bash
   curl -i http://localhost:3000/api/health -H "Authorization: Bearer wrong_token"
   ```

   **With Hardcoded Token (Returns `200 OK`):**
   ```bash
   curl -i http://localhost:3000/api/health -H "Authorization: Bearer sec_react_health_token_6e5d4c3b2a1f0e9d8c7b"
   ```

   *PowerShell alternative:*
   ```powershell
   Invoke-RestMethod -Uri "http://localhost:3000/api/health" -Headers @{ Authorization = "Bearer sec_react_health_token_6e5d4c3b2a1f0e9d8c7b" }
   ```

### Option 3: Test Secret Scanners

To verify if your scanner flags the hardcoded React environment leaks and server route secrets:

- **Gitleaks**:
  ```powershell
  gitleaks detect --source ./react-secret-fixture -v
  ```
- **TruffleHog**:
  ```powershell
  trufflehog filesystem ./react-secret-fixture
  ```
- **GitHub Push Protection**:
  ```powershell
  git add react-secret-fixture/
  git commit -m "test: add react secret fixture and health check api"
  git push origin main
  ```

