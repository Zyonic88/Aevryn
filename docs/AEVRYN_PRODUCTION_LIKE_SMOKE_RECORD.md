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
Latest attempt: 2026-07-01 local PostgreSQL and R2 smoke passed
```

Production-like smoke is partially complete.

The latest attempt verified the production startup contract, local PostgreSQL Project Database smoke, and Cloudflare R2 storage smoke with metadata-only output.

Hosted browser/API smoke is still not complete.

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
| API startup | production app starts with local-only adapters rejected | Not run in production-like environment |
| HTTPS/CORS | public origins are explicit and HTTPS-only | Not run in production-like environment |
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
Reason: Local production-style config, PostgreSQL, and R2 smoke passed, but hosted production-like browser/API smoke has not passed.
```
