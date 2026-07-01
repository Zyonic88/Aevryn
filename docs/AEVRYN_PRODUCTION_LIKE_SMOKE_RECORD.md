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
Latest attempt: 2026-07-01 local fail-closed check
```

Production-like smoke is not complete.

The latest attempt verified that the smoke commands fail closed when the required production-like environment is not loaded.

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

# Required Production-Like Environment

The next successful smoke attempt needs a release-candidate or hosted environment with production-style configuration loaded from the deployment secret manager.

Required configuration families:

* `AEVRYN_DEPLOYMENT_ENV=production`
* PostgreSQL Project Database settings
* Cloudflare R2 storage settings
* Supabase managed identity settings
* session authority and session secret settings
* HTTPS, HSTS, public API, and public frontend base URL settings
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
| Production config check | `startup_contract=ready`, `secrets_printed=0` | Not run in production-like environment |
| PostgreSQL smoke | create/read/delete synthetic metadata record succeeds | Not run in production-like environment |
| R2 storage smoke | write/read/delete tiny synthetic private object succeeds | Not run in production-like environment |
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
Reason: Production-like smoke has not passed in a hosted or fully configured production-like environment.
```
