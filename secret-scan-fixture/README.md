# secret-scan-fixture

Test fixture for secret-scanning tools (Node.js, React, Angular, infra).

**Every credential in this repo is FAKE.** They are random strings shaped like real provider
secrets so scanners flag them. Nothing here is valid anywhere. Do not put real secrets in this repo.

| Path | Purpose |
|------|---------|
| backend/ | Node/Express API with hardcoded secrets |
| frontend-react/ | React app with a hardcoded key |
| frontend-angular/ | Angular app with a hardcoded key in environment.prod.ts |
| infra/ | docker-compose + terraform vars (same fake AWS key as backend: cross-file case) |
| deploy/id_rsa.pem | Fake private key block |
| .env.example, backend/src/safe.js | Decoys: must NOT be flagged |
