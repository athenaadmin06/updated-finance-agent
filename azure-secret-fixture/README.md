# azure-secret-fixture

Test fixture for secret-scanning tools (Python + Java, Azure services, Azure Key Vault focus).

**Every credential in this repo is FAKE.** They are random strings shaped like real Azure secrets.
Nothing here is valid anywhere. Do not put real secrets in this repo.

| Path | Purpose |
|------|---------|
| python-app/ | Python app with hardcoded Azure AD client secret, storage key, SAS token, Cosmos key, Azure OpenAI key |
| java-app/ | Java/Spring app with hardcoded Azure credentials in code and application.yml |
| deploy/ | Fake service-principal private key |
| .github/workflows/deploy.yml | Hardcoded service-principal JSON |
| python-app/keyvault_good.py, java-app/.../KeyVaultGood.java | Decoys: correct Key Vault usage, must NOT be flagged |
