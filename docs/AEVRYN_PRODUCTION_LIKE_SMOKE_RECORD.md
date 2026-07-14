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
Latest attempt: 2026-07-01 hosted managed identity and project smoke passed
```

Production-like smoke is partially complete.

The latest attempt verified the production startup contract, local PostgreSQL Project Database smoke, and Cloudflare R2 storage smoke with metadata-only output.

Hosted Cloud Run API health smoke has passed.

Hosted custom-domain API health smoke has passed.

Local frontend gates have passed with the hosted API base URL configured.

Hosted frontend/API custom-domain header smoke has passed.

Hosted browser-flow smoke verified login/register availability, protected frontend-route redirects, protected API-route authentication, managed-identity login completion, authenticated project create/read/list, and clean browser console output.

Hosted import processing, monitoring workflow status, export preview, production-safe worker posture, log review, and final release-candidate signoff are still not complete.

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
* hosted log and monitoring settings
* security alert routing settings
* metadata-only logging settings

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
BLOCKED for Cloudflare Pages hosted frontend/API smoke.
BLOCKED for managed identity browser flow smoke.
BLOCKED for creator workflow smoke.
```

No API key, storage credential, database URL, Supabase service-role key, worker key, session secret, source prose, or AI payload was printed.

---

# Attempt 2026-07-01 - Hosted Frontend/API Custom-Domain Smoke

Environment:

```text
Execution surface: Cloudflare Pages and Google Cloud Run custom domains
Frontend project: aevryn-web
Frontend preview URL: https://84f1e9e9.aevryn-web.pages.dev
Frontend custom domain: https://app.aevryn.ai
API custom domain: https://api.aevryn.ai
Result: hosted frontend/API custom-domain header smoke passed
```

Commands run:

```powershell
curl.exe -I https://app.aevryn.ai
curl.exe -i -H "Origin: https://app.aevryn.ai" https://api.aevryn.ai/v2/health
```

Observed result:

```text
https://app.aevryn.ai returned HTTP OK.
https://api.aevryn.ai/v2/health returned status OK.
API CORS returned access-control-allow-origin: https://app.aevryn.ai.
```

Interpretation:

```text
PASS for Cloudflare Pages custom-domain frontend availability.
PASS for API CORS allowing the intended frontend origin.
BLOCKED for managed identity browser flow smoke.
BLOCKED for creator workflow smoke.
```

No API key, storage credential, database URL, Supabase service-role key, worker key, session secret, source prose, or AI payload was printed.

Local-only project database paths, local import storage paths, local JSON authentication, local-only secrets, in-memory workers, local-only logs, and ambiguous environment names must remain rejected in production mode.

---

# Attempt 2026-07-01 - Hosted Browser-Flow Smoke

Environment:

```text
Execution surface: in-app browser plus metadata-only hosted API checks
Frontend custom domain: https://app.aevryn.ai
API custom domain: https://api.aevryn.ai
Result: browser-flow smoke partially passed; managed identity login completion blocked
```

Browser actions:

```text
Opened https://app.aevryn.ai.
Opened https://app.aevryn.ai/dashboard while signed out.
Opened https://app.aevryn.ai/register.
Submitted a synthetic fake login on https://app.aevryn.ai/login.
```

Command run:

```powershell
curl.exe -i -H "Origin: https://app.aevryn.ai" https://api.aevryn.ai/v2/projects
```

Observed result:

```text
https://app.aevryn.ai redirected to /login.
Login page loaded.
Register page loaded.
Unauthenticated /dashboard access redirected to /login.
Browser console warnings/errors: none observed.
No local auth/session storage keys were created by the failed login attempt.
Synthetic fake login stayed on /login and returned: Managed identity provider owns login.
Unauthenticated GET /v2/projects returned 401 session_required.
API CORS returned access-control-allow-origin: https://app.aevryn.ai.
API response included x-request-id.
```

Interpretation:

```text
PASS for hosted login/register shell availability.
PASS for protected frontend route redirect while unauthenticated.
PASS for protected API route requiring bearer managed identity.
PASS for metadata-only unauthorized API error.
PASS for clean browser console output during the checked flow.
BLOCKED for managed identity login completion.
BLOCKED for creator workflow smoke.
```

No real user credentials, API key, storage credential, database URL, Supabase service-role key, worker key, session secret, source prose, or AI payload was used or printed.

---

# Attempt 2026-07-01 - Hosted Managed Identity And Project Smoke

Environment:

```text
Execution surface: in-app browser against hosted frontend and API
Frontend custom domain: https://app.aevryn.ai
API custom domain: https://api.aevryn.ai
Managed identity provider: Supabase Auth
Result: managed identity login and authenticated project create/read/list passed
```

Browser actions:

```text
Logged in with a Supabase-managed test user.
Opened https://app.aevryn.ai/dashboard.
Created project RC Smoke Test Project.
Opened the created project workspace.
Returned to dashboard and verified the project appears in the project list.
```

Observed result:

```text
Dashboard loaded while authenticated.
API Health returned status ok, engine Aevryn, API v2, storage configured.
API Capabilities loaded with 43 routes, 5 auth routes, and 7 supported formats.
Projects route no longer returned Supabase JWT algorithm errors.
Empty project state displayed before project creation.
Created project route loaded at /projects/project_39860ae9_3f6f_4f5c_a487_ab907ea5918e.
Project workspace displayed the expected Overview, Story, Import, Characters, World, Timeline, Scenes, Continuity, Prompt Packs, Exports, and Settings sections.
Dashboard project list displayed RC Smoke Test Project after creation.
Browser console warnings/errors: none observed.
```

Interpretation:

```text
PASS for managed identity login completion.
PASS for authenticated project creation.
PASS for authenticated project detail read.
PASS for authenticated project list read.
PASS for clean browser console output during the checked flow.
OPEN for import processing workflow smoke in the hosted environment.
OPEN for monitoring status and export preview smoke in the hosted environment.
```

No real user password, API key, storage credential, database URL, Supabase service-role key, worker key, session secret, source prose, full AI payload, private URL, username, or machine-local path was printed.

---

# Attempt 2026-07-02 - Hosted Import Worker Boundary Regression

Environment:

```text
Execution surface: local test runner and production frontend build
Frontend behavior under test: hosted browser import processing
Result: hosted browser no longer calls protected worker-drain endpoint
```

Observed production issue:

```text
Hosted login, project creation, ten-chapter import inspection, and import save passed.
Submitting processing created the run successfully.
The hosted browser then called POST /v2/workers/process and received 401 Unauthorized.
The browser surfaced the old local-development API-unreachable wording.
```

Regression coverage added:

```text
Hosted browser sessions queue processing runs without draining worker jobs from the browser.
Localhost sessions retain browser worker draining for local alpha iteration.
Network failures use hosted-safe wording instead of local API server wording.
Backend can opt into a hosted alpha server-side worker drain during run submission.
```

Commands run:

```powershell
cd C:\Users\enigm\Documents\Aevryn\web
npm.cmd test -- --run src/App.test.tsx src/api/client.test.ts
npm.cmd test -- --run
npm.cmd run build
python -m pytest tests/test_auth_api.py -q
python -m pytest
```

Observed result:

```text
Focused frontend tests passed: 95 tests.
Full frontend suite passed: 152 tests.
Frontend production build passed.
Focused backend auth/API tests passed: 45 tests.
Full backend suite passed: 859 tests.
```

Interpretation:

```text
PASS for preventing hosted browsers from calling the protected worker processor.
PASS for hosted-safe API unreachable copy.
PASS for the hosted alpha nonblocking auto-process bridge contract.
OPEN for deploying and smoke-testing the bridge on Cloud Run.
OPEN for replacing the alpha bridge with a production-safe persistent worker runner.
```

No real user password, API key, storage credential, database URL, Supabase service-role key, worker key, session secret, source prose, full AI payload, private URL, username, or machine-local path was printed.

---

# Attempt 2026-07-14 - Hosted Creator Workflow Smoke Plan

Environment:

```text
Execution surface: in-app browser against hosted frontend and API
Frontend custom domain: https://app.aevryn.ai
API custom domain: https://api.aevryn.ai
Managed identity provider: Supabase Auth
Provider mode: hosted configured provider
Status: Planned
```

This attempt should verify the hosted workflow that remained open after the July 1 and July 2 smoke passes.

Required browser actions:

```text
Log in with the managed test user.
Open the dashboard.
Create a release-candidate smoke project.
Create or select a story.
Upload owner-approved test chapters.
Inspect the import.
Save the import.
Submit processing once.
Observe project run state without browser-side worker draining.
Wait for processing to finish or fail clearly.
Open Monitoring and confirm workflow state is API-provided.
Review Characters, World, Timeline, Scenes, Continuity, Prompt Packs, Exports, and Settings.
Create an export preview if the hosted workflow exposes the export action.
Refresh the browser and confirm API-backed state restores.
Delete the smoke project and confirm it disappears from active product surfaces.
```

Required metadata-only checks:

```text
No full source prose in browser diagnostics, monitoring, API errors, or logs.
No full AI provider response in browser diagnostics, monitoring, API errors, or logs.
No credentials, tokens, private URLs, hostnames, usernames, or machine-local paths in visible output.
No creator-facing source-backed placeholder text, import bundle IDs, source IDs, or evidence anchor IDs.
No stuck "submitting" or "processing" state after the run finishes or fails.
No duplicate processing run is created from one submit action.
Browser console warnings/errors are reviewed.
```

Result:

```text
Not run.
```

Interpretation:

```text
OPEN for hosted import processing workflow smoke.
OPEN for monitoring workflow status smoke.
OPEN for export preview smoke.
OPEN for production-safe worker posture evidence.
OPEN for hosted log review.
```

---

# Required Successful Smoke

A successful production-like smoke must record:

| Check | Expected Result | Status |
| --- | --- | --- |
| Production config check | `startup_contract=ready`, `secrets_printed=0` | Passed locally |
| PostgreSQL smoke | create/read/delete synthetic metadata record succeeds | Passed locally |
| R2 storage smoke | write/read/delete tiny synthetic private object succeeds | Passed locally |
| API startup | production app starts with local-only adapters rejected | Passed on Cloud Run |
| HTTPS/CORS | public origins are explicit and HTTPS-only | Health endpoint passed on Cloud Run and api.aevryn.ai; app.aevryn.ai frontend header smoke and API CORS origin check passed |
| Managed identity | protected routes require managed identity tokens | Passed for unauthenticated redirects/API 401 and hosted Supabase login completion |
| Worker processing | import processing completes through production-safe worker posture | Not run in production-like environment |
| Monitoring | workflow state is observable through metadata-only status | Not run in production-like environment |
| Export preview | export preview works through storage-reference boundaries | Not run in production-like environment |
| Authenticated project workflow | create/read/list project metadata through hosted API | Passed for RC Smoke Test Project |
| Logs | no manuscripts, credentials, tokens, private URLs, hostnames, usernames, or machine-local paths | Passed for the checked hosted browser/API smoke; still required for import/worker smoke |

---

# Next Action

Run the July 14 hosted creator workflow smoke plan against the production-like hosted frontend and API.

If local production-style smoke must be repeated before the hosted run, use metadata-only commands:

```powershell
$env:PYTHONPATH="src"
python -m aevryn.cli production-config-check
python -m aevryn.cli project-db-smoke
python -m aevryn.cli storage-smoke
```

Then record the hosted browser/API result in this document or in a dated release-candidate run record.

---

# Public Beta Decision

```text
Public beta: Blocked
Reason: Local production-style config, PostgreSQL, R2, hosted Cloud Run API health smoke, custom-domain API health smoke, hosted frontend/API custom-domain header smoke, unauthenticated browser-route/API protection checks, managed-identity login completion, and authenticated project create/read/list smoke passed. Hosted import processing, monitoring workflow status, export preview, production-safe worker posture, log review, and final release-candidate signoff have not passed.
```
