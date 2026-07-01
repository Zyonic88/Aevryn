# Aevryn Production-Like Smoke Record

> Built by **Aetherra Labs**

This document records production-like smoke attempts for V2 Release Candidate Readiness Gate 3.

It is separate from the final release-candidate run record because smoke attempts may happen more than once before the final public-beta decision.

---

# Status

```text
Record type: Production-Like Smoke Attempt Log
Status: Started
Public beta: Blocked
Latest attempt: 2026-07-01 hosted custom-domain API health smoke passed
```

Production-like smoke is partially complete.

The latest attempt verified the production startup contract, local PostgreSQL Project Database smoke, and Cloudflare R2 storage smoke with metadata-only output.

Hosted Cloud Run API health smoke has passed.

Hosted custom-domain API health smoke has passed.

Local frontend gates have passed with the hosted API base URL configured.

Hosted browser/API, managed-identity, and workflow smoke are still not complete.

---

# Core Rule

```text
Production-like smoke proves configuration and workflow safety. It does not bypass production gates.
```

Smoke commands must remain metadata-only.

They must not print database URLs, API keys, storage keys, worker keys, Supabase keys, session secrets, credentials, source prose, full AI payloads, private URLs, hostnames, usernames, or machine-local paths.

---

# Attempt 2026-07-01 - Local Fail-Closed Check

Environment:

```text
Execution surface: local Codex shell
Hosted deployment: not used
Production-like environment variables: not loaded in this process
Result: fail-closed behavior verified, production-like smoke not passed
```

Commands attempted:

```powershell
python -m aevryn.cli production-config-check
python -m aevryn.cli project-db-smoke
python -m aevryn.cli storage-smoke
```

Observed results:

```text
production-config-check: Error: AEVRYN_DEPLOYMENT_ENV=production is required.
project-db-smoke: Error: AEVRYN_PROJECT_DATABASE_URL is required in the process environment.
storage-smoke: Error: AEVRYN_STORAGE_PROVIDER is required in the process environment.
```

Interpretation:

```text
PASS for fail-closed behavior.
FAIL/blocked for production-like smoke completion.
```

The commands stopped before connecting to PostgreSQL, Cloudflare R2, Supabase, worker infrastructure, hosted logs, or hosted monitoring.

No secret values were printed.

No source prose was used.

---

# Attempt 2026-07-01 - Local PostgreSQL And R2 Smoke

Environment:

```text
Execution surface: local PowerShell
Hosted deployment: not used
PostgreSQL target: local aevryn_dev database
Object storage target: private Cloudflare R2 aevryn-dev bucket
Result: production config, PostgreSQL, and R2 smoke passed
```

Commands run:

```powershell
python -m aevryn.cli production-config-check
python -m aevryn.cli project-db-smoke
python -m aevryn.cli storage-smoke
```

Observed metadata-only results:

```text
deployment_env=production
startup_contract=ready
public_beta=not_approved_until_gate_signoff
secrets_printed=0
ok=production_config_contract_checked
adapter=postgresql
schema=bootstrapped
records_created=1
records_deleted=1
ok=project_database_postgresql_smoke_completed
adapter=r2
bucket=aevryn-dev
bytes_written=28
objects_created=1
objects_deleted=1
ok=storage_r2_smoke_completed
```

Interpretation:

```text
PASS for local production-style config contract.
PASS for PostgreSQL metadata smoke.
PASS for private R2 object-storage smoke.
BLOCKED for hosted production-like browser/API smoke.
```

No database URL, database password, API key, storage access key, storage secret key, Supabase key, worker key, session secret, source prose, or AI payload was printed.

---

# Attempt 2026-07-01 - Hosted Cloud Run API Health Smoke

Environment:

```text
Execution surface: Google Cloud Run
Service: aevryn-api
Region: us-central1
Revision: aevryn-api-00003-9v4
Service URL: https://aevryn-api-561437810621.us-central1.run.app
Result: hosted API health smoke passed
```

Commands run:

```powershell
curl.exe https://aevryn-api-561437810621.us-central1.run.app/v2/health
curl.exe -i https://aevryn-api-561437810621.us-central1.run.app/v2/health
```

Observed result:

```text
/v2/health returned status OK.
Header/status check returned status OK.
```

Interpretation:

```text
PASS for hosted Cloud Run API startup.
PASS for HTTPS health endpoint availability.
BLOCKED for Cloudflare Pages frontend-to-API smoke.
BLOCKED for managed identity browser flow smoke.
BLOCKED for creator workflow smoke.
```

No database URL, database password, API key, storage access key, storage secret key, Supabase key, worker key, session secret, source prose, or AI payload was printed.

---

# Attempt 2026-07-01 - Hosted Custom-Domain API Health Smoke

Environment:

```text
Execution surface: Google Cloud Run custom domain
Service: aevryn-api
Region: us-central1
Domain: api.aevryn.ai
DNS: api CNAME ghs.googlehosted.com.
Certificate: Google-managed certificate provisioned
Result: hosted custom-domain API health smoke passed
```

Commands run:

```powershell
Resolve-DnsName api.aevryn.ai -Type CNAME
curl.exe -i https://api.aevryn.ai/v2/health
curl.exe -i https://aevryn-api-561437810621.us-central1.run.app/v2/health
```

Observed result:

```text
api.aevryn.ai resolved to ghs.googlehosted.com.
https://api.aevryn.ai/v2/health returned status OK.
Direct Cloud Run service URL also returned status OK.
```

Interpretation:

```text
PASS for api.aevryn.ai custom-domain DNS.
PASS for Google-managed certificate provisioning.
PASS for custom-domain HTTPS health endpoint availability.
BLOCKED for Cloudflare Pages frontend-to-API smoke.
BLOCKED for managed identity browser flow smoke.
BLOCKED for creator workflow smoke.
```

No database URL, database password, API key, storage access key, storage secret key, Supabase key, worker key, session secret, source prose, or AI payload was printed.

---

# Required Production-Like Environment

The next successful smoke attempt needs a release-candidate or hosted environment with production-style configuration loaded from the deployment secret manager.

Required configuration families:

* `AEVRYN_DEPLOYMENT_ENV=production`
* `AEVRYN_PROJECT_DATABASE_ADAPTER=postgresql`
* PostgreSQL Project Database settings
* Cloudflare R2 storage settings
* Supabase managed identity settings
* session authority and session secret settings
* HTTPS, HSTS, public API, and public frontend base URL settings
* explicit HTTPS-only `AEVRYN_API_ALLOWED_ORIGINS`
* managed worker runtime and queue settings

---

# Attempt 2026-07-01 - Local Frontend Hosted-API Build Smoke

Environment:

```text
Execution surface: local PowerShell
Frontend base: local Vite production build
API base: https://api.aevryn.ai
Result: local frontend hosted-API build smoke passed
```

Commands run:

```powershell
cd C:\Users\enigm\Documents\Aevryn\web
$env:VITE_AEVRYN_API_URL="https://api.aevryn.ai"
npm.cmd run build
npm.cmd run lint
npm.cmd run test
```

Observed result:

```text
Frontend production build passed.
Frontend lint passed.
Frontend test suite passed: 146 tests.
```

Interpretation:

```text
PASS for local production build against hosted API configuration.
PASS for frontend lint and tests.
BLOCKED for Cloudflare Pages hosted browser/API smoke.
BLOCKED for managed identity browser flow smoke.
BLOCKED for creator workflow smoke.
```

No API key, storage credential, database URL, Supabase service-role key, worker key, session secret, source prose, or AI payload was printed.
* hosted log and monitoring settings
* security alert routing settings
* metadata-only logging settings

Local-only project database paths, local import storage paths, local JSON authentication, local-only secrets, in-memory workers, local-only logs, and ambiguous environment names must remain rejected in production mode.

---

# Required Successful Smoke

A successful production-like smoke must record:

| Check | Expected Result | Status |
| --- | --- | --- |
| Production config check | `startup_contract=ready`, `secrets_printed=0` | Passed locally |
| PostgreSQL smoke | create/read/delete synthetic metadata record succeeds | Passed locally |
| R2 storage smoke | write/read/delete tiny synthetic private object succeeds | Passed locally |
| API startup | production app starts with local-only adapters rejected | Passed on Cloud Run |
| HTTPS/CORS | public origins are explicit and HTTPS-only | Health endpoint passed on Cloud Run and api.aevryn.ai; browser CORS smoke not complete |
| Managed identity | protected routes require managed identity tokens | Not run in production-like environment |
| Worker processing | import processing completes through production-safe worker posture | Not run in production-like environment |
| Monitoring | workflow state is observable through metadata-only status | Not run in production-like environment |
| Export preview | export preview works through storage-reference boundaries | Not run in production-like environment |
| Logs | no manuscripts, credentials, tokens, private URLs, hostnames, usernames, or machine-local paths | Not run in production-like environment |

---

# Next Action

Run the smoke commands again only after the production-like environment has the required secret-backed settings loaded:

```powershell
$env:PYTHONPATH="src"
python -m aevryn.cli production-config-check
python -m aevryn.cli project-db-smoke
python -m aevryn.cli storage-smoke
```

Then run the browser/API smoke against the production-like API and record the result in this document or in a dated release-candidate run record.

---

# Public Beta Decision

```text
Public beta: Blocked
Reason: Local production-style config, PostgreSQL, R2, hosted Cloud Run API health smoke, and custom-domain API health smoke passed, but frontend, managed-identity, and creator workflow smoke have not passed.
```
