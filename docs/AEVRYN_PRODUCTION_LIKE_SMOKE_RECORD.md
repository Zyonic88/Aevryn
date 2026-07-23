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
Latest attempt: 2026-07-17 provider and observability config gates passed
```

Production-like smoke is partially complete.

The latest attempt verified the production startup contract, local PostgreSQL Project Database smoke, and Cloudflare R2 storage smoke with metadata-only output.

Hosted Cloud Run API health smoke has passed.

Hosted custom-domain API health smoke has passed.

Local frontend gates have passed with the hosted API base URL configured.

Hosted frontend/API custom-domain header smoke has passed.

Hosted browser-flow smoke verified login/register availability, protected frontend-route redirects, protected API-route authentication, managed-identity login completion, authenticated project create/read/list, and clean browser console output.

Hosted import processing, monitoring workflow status, export creation, production-safe worker posture, and hosted browser UI sweep have passed for the retry smoke.

Hosted restricted audit role verification has passed.

Hosted provider and observability configuration gates have passed.

Final release-candidate signoff is still not complete.

---

# Core Rule

```text
Production-like smoke proves configuration and workflow safety. It does not bypass production gates.
```

Smoke commands must remain metadata-only.

They must not print database URLs, API keys, storage keys, worker keys, Supabase keys, session secrets, credentials, source prose, full AI payloads, private URLs, hostnames, usernames, or machine-local paths.

---

# Attempt 2026-07-14 - Hosted Audit Gates

Environment:

```text
Execution surface: local PowerShell using Google Secret Manager for the hosted database URL
Hosted deployment: production-like Cloud Run database target
Output boundary: metadata-only CLI output
Result: audit integrity passed; append-only access verification failed
```

Commands run:

```powershell
python -m aevryn.cli audit-ledger-verify
python -m aevryn.cli audit-access-report
python -m aevryn.cli audit-access-verify
```

Observed metadata-only results:

```text
adapter=postgresql
ledger=audit
records_verified=0
secrets_printed=0
ok=audit_ledger_postgresql_integrity_verified
adapter=postgresql
ledger=audit
table_exists=true
can_select=true
can_insert=true
can_update=true
can_delete=true
secrets_printed=0
ok=audit_access_metadata_reported
audit-access-verify: Error: PostgreSQL audit append-only contract failed: UPDATE privilege is present.
```

Interpretation:

```text
PASSED for hosted audit table existence.
PASSED for hosted audit hash-chain integrity verification.
PASSED for metadata-only audit-gate output.
FAILED for least-privilege append-only audit access because UPDATE and DELETE privileges are present.
BLOCKED for public beta until Cloud Run uses a restricted PostgreSQL application role or equivalent database policy that preserves SELECT/INSERT while removing UPDATE/DELETE on audit_ledger_records.
```

No database URL, database credential, storage key, API key, Supabase key, role name, username, hostname, source prose, full AI payload, or audit row payload was printed.

---

# Attempt 2026-07-17 - Hosted Restricted Audit Role Verification

Environment:

```text
Execution surface: local PowerShell using Google Secret Manager for the hosted database URL
Hosted deployment: production-like Cloud Run database target
Database posture: restricted runtime PostgreSQL role
Output boundary: metadata-only CLI output
Result: audit integrity passed; append-only access verification passed
```

Commands run:

```powershell
python -m aevryn.cli audit-ledger-verify
python -m aevryn.cli audit-access-report
python -m aevryn.cli audit-access-verify
```

Observed metadata-only results:

```text
adapter=postgresql
ledger=audit
records_verified=1338
secrets_printed=0
ok=audit_ledger_postgresql_integrity_verified
adapter=postgresql
ledger=audit
table_exists=true
can_select=true
can_insert=true
can_update=false
can_delete=false
can_truncate=false
is_table_owner=false
secrets_printed=0
ok=audit_access_metadata_reported
adapter=postgresql
ledger=audit
table_exists=true
can_select=true
can_insert=true
can_update=false
can_delete=false
can_truncate=false
is_table_owner=false
secrets_printed=0
ok=audit_access_append_only_verified
```

Interpretation:

```text
PASSED for hosted audit hash-chain integrity verification.
PASSED for metadata-only audit-gate output.
PASSED for least-privilege append-only audit access.
PASSED for restricted runtime role non-ownership of audit history.
```

No database URL, database credential, storage key, API key, Supabase key, role
name, username, hostname, source prose, full AI payload, or audit row payload was
printed.

---

# Attempt 2026-07-17 - Provider And Observability Config Gates

Environment:

```text
Execution surface: local PowerShell using Google Secret Manager for hosted production-like secrets
Hosted deployment: production-like Cloud Run configuration target
Output boundary: metadata-only CLI output
Result: provider config passed; observability config passed
```

Commands run:

```powershell
python -m aevryn.cli provider-config-check
python -m aevryn.cli observability-config-check
```

Observed provider metadata-only result:

```text
deployment_env=production
provider=openai
extraction_mode=openai
model=gpt-5.4-mini
timeout_seconds=90.0
max_response_bytes=1048576
request_storage=disabled
responses_store=false
provider_review=required
public_beta=blocked_until_provider_review
secrets_printed=0
ok=provider_config_contract_checked
```

Observed observability metadata-only result:

```text
deployment_env=production
log_destination=hosted
monitoring_destination=hosted
log_retention_days=30
monitoring_retention_days=30
security_alerts_enabled=true
metadata_only_logging=true
bounded_hosted_log_review=required
public_beta=blocked_until_bounded_hosted_log_review
secrets_printed=0
ok=observability_config_contract_checked
```

Interpretation:

```text
PASSED for provider configuration metadata.
PASSED for provider request storage disabled posture.
PASSED for Responses API store=false posture.
PASSED for hosted observability configuration metadata.
OPEN for owner/legal/provider review.
OPEN for final bounded hosted log review.
```

No database URL, database credential, storage key, API key, Supabase key, OpenAI
key, session secret, worker key, source prose, full provider prompt, full
provider response, or audit row payload was printed.

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
Status: Failed
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
FAILED.

Run date: 2026-07-14.
Project: RC Smoke 2026-07-14.
Project ID: project_447d9366_5a2a_4b38_8c28_ab7bf41de973.
Input: 10 owner-approved TXT chapters, 82,024 bytes.
Inspected import: 10 chapters, 19 scenes, 327 paragraphs, 1,296 evidence anchors.
Save import: passed.
Submit processing: passed.
Worker state: running state appeared with queued/processing/snapshot/output stepper.
Final run state: failed.
Failure summary: AI extraction timed out while reading the provider response. Retry with a smaller chapter batch or increase the provider timeout for large imports.
Monitoring state: API health ok; project run status failed; worker failed; queued jobs 0; running jobs 0; latest failure visible.
Refresh restore: passed. Monitoring restored failed state after browser refresh.
Browser console: no warning/error entries observed during monitoring failure review.
Cleanup: smoke project deleted from dashboard and no API error appeared during deletion.
```

Interpretation:

```text
BLOCKED for hosted import processing workflow smoke until provider timeout behavior is hardened.
PASSED for hosted import inspection and save workflow.
PASSED for monitoring workflow status visibility after a failed run.
PASSED for refresh restore of API-backed failed state.
PASSED for smoke project deletion cleanup.
NOT RUN for successful post-processing workspace output review because processing failed.
NOT RUN for export preview because no snapshot was created.
FINDING: Monitoring displayed latest import as aevryn_import_bundle.txt. This is metadata only, but it is still creator-facing internal naming noise and should be hidden or replaced with a human label.
NEXT FIX: harden hosted extraction timeout behavior for 10-chapter imports and remove internal import bundle filename from monitoring.
```

---

# Attempt 2026-07-14 - Hosted Creator Workflow Smoke Retry

Environment:

```text
Execution surface: in-app browser against hosted frontend and API
Frontend custom domain: https://app.aevryn.ai
API custom domain: https://api.aevryn.ai
Managed identity provider: Supabase Auth
Provider mode: hosted configured provider
Cloud Run revision after timeout hardening: aevryn-api-00021-lk7
Status: Passed
```

Result:

```text
PASSED.

Run date: 2026-07-14.
Project: RC Smoke Retry 2026-07-14.
Project ID: project_30c12069_caf1_43da_b91d_de2887097e77.
Input: 10 owner-approved TXT chapters, 82,024 bytes.
Inspected import: 10 chapters, 19 scenes, 327 paragraphs, 1,296 evidence anchors.
Save import: passed.
Submit processing: passed.
Worker state: queued/processing/snapshot/output stepper appeared.
Final run state: succeeded.
Snapshot state: canon snapshot ready.
Duplicate run check: one processing run was created from one submit action.
Monitoring state: API health ok; project run status succeeded; worker idle; queued jobs 0; running jobs 0; latest failure absent.
Monitoring import label: latest import displayed as Chapter import, not the internal bundle filename.
Refresh restore: passed. Monitoring restored succeeded state after browser refresh.
Workspace sweep: Overview, Story, Import, Characters, World, Timeline, Scenes, Continuity, Prompt Packs, Exports, and Settings loaded without known internal-noise blockers.
Export creation: passed. A JSON canon snapshot export was created and displayed with a download action.
Export monitoring: export availability yes; export count 1; recent event recorded Export Created.
Browser console: no warning/error entries observed during monitoring and workspace review.
Cleanup: passed. Project deletion removed the smoke project from the dashboard, reduced the dashboard count to 2 projects, and direct navigation to the deleted project returned the dashboard without API errors.
```

Known non-blocking findings:

```text
Identity review summaries appear across several output tabs. This is truthful metadata, but visually repetitive and should be considered for UX hardening.
Some output tabs still contain expected Unknown/No-data states where canon evidence is incomplete.
```

Interpretation:

```text
PASSED for hosted import inspection and save workflow.
PASSED for hosted import processing workflow.
PASSED for monitoring workflow status visibility after a successful run.
PASSED for refresh restore of API-backed succeeded state.
PASSED for export creation from the latest canon snapshot.
PASSED for metadata-only workflow events.
PASSED for hiding internal import bundle filenames from Monitoring.
PASSED for the checked browser console warnings/errors.
PASSED for smoke project deletion cleanup.
PASSED for internal release-candidate signoff.
OPEN for public-beta approval.
```

---

# Attempt 2026-07-14 - Hosted Log Review

Environment:

```text
Execution surface: Google Cloud Run bounded service-log sample
Service: aevryn-api
Region: us-central1
Sample size: 200 recent service-log lines
Status: Passed with metadata-only access-log finding
```

Observed metadata:

```text
Request logs included public API routes, HTTP methods, HTTP statuses, project IDs, story IDs, and Google-managed proxy addresses.
Request logs did not include manuscript text.
Request logs did not include full AI provider responses.
Request logs did not include credentials, tokens, secret values, database URLs, storage keys, Supabase keys, worker keys, session secrets, usernames, or machine-local paths.
No warning/error entries appeared in the sampled hosted service logs.
```

Finding:

```text
Cloud Run and Uvicorn access logs include route-level workflow metadata.
This is acceptable for the current production-like smoke because it is metadata-only, but it should remain part of future privacy review before public beta.
```

Interpretation:

```text
PASSED for hosted log review of the checked import, monitoring, and export smoke window.
PASSED for no source prose in sampled hosted logs.
PASSED for no full AI payloads in sampled hosted logs.
PASSED for no secret values in sampled hosted logs.
OPEN for hosted retention and final bounded-log verification against `docs/AEVRYN_PRODUCTION_OBSERVABILITY_POLICY.md` before public beta.
```

---

# Required Successful Smoke

A successful production-like smoke must record:

| Check | Expected Result | Status |
| --- | --- | --- |
| Production config check | `startup_contract=ready`, `secrets_printed=0` | Passed locally |
| Provider config check | explicit provider mode, key presence, model, timeout, response-size boundary, no provider keys printed | Passed with metadata-only output; provider review remains required |
| Observability config check | hosted logs/monitoring, bounded retention, metadata-only logging, security alerts | Passed with metadata-only output; bounded hosted log review remains required |
| PostgreSQL smoke | create/read/delete synthetic metadata record succeeds | Passed locally |
| R2 storage smoke | write/read/delete tiny synthetic private object succeeds | Passed locally |
| API startup | production app starts with local-only adapters rejected | Passed on Cloud Run |
| HTTPS/CORS | public origins are explicit and HTTPS-only | Health endpoint passed on Cloud Run and api.aevryn.ai; app.aevryn.ai frontend header smoke and API CORS origin check passed |
| Managed identity | protected routes require managed identity tokens | Passed for unauthenticated redirects/API 401 and hosted Supabase login completion |
| Worker processing | import processing completes through production-safe worker posture | Passed for hosted ten-chapter smoke retry |
| Monitoring | workflow state is observable through metadata-only status | Passed for hosted successful run and export event |
| Export preview | export preview works through storage-reference boundaries | Passed for hosted JSON snapshot export creation |
| Authenticated project workflow | create/read/list project metadata through hosted API | Passed for RC Smoke Test Project |
| Logs | no manuscripts, credentials, tokens, private URLs, usernames, machine-local paths, or full AI payloads | Passed for bounded hosted Cloud Run log review; route-level metadata remains expected access-log data |
| Audit ledger integrity | `audit-ledger-verify` passes without printing secrets | Passed against hosted database target |
| Audit access report | `audit-access-report` reports metadata-only table and privilege state | Passed; table exists and restricted runtime role can select/insert but cannot update/delete/truncate/own audit records |
| Audit append-only access | `audit-access-verify` rejects update/delete audit privileges | Passed with restricted runtime role |

---

# Next Action

Complete the remaining release-candidate readiness checks that are outside the browser smoke:

```text
Verify hosted retention and bounded-log behavior against the production observability policy before public beta.
Complete provider owner/legal review before provider-backed extraction is public-beta approved.
Complete public-facing legal, trust, and support publication before public beta.
Complete backup/restore/audit readiness before public beta.
Run `docs/AEVRYN_BACKUP_RESTORE_RUNBOOK.md` in an isolated restore target and complete a dated restore/audit drill record.
The 2026-07-17 restore source preflight is recorded in
`docs/AEVRYN_RESTORE_AUDIT_DRILL_2026_07_17.md`; it does not close the restore
gate because no isolated restore target has been verified.
Continue prompt-pack and output UX polish before public beta positioning.
```

If local production-style smoke must be repeated before final signoff, use metadata-only commands:

```powershell
$env:PYTHONPATH="src"
python -m aevryn.cli production-config-check
python -m aevryn.cli provider-config-check
python -m aevryn.cli observability-config-check
python -m aevryn.cli project-db-smoke
python -m aevryn.cli storage-smoke
python -m aevryn.cli audit-ledger-verify
python -m aevryn.cli audit-access-report
python -m aevryn.cli audit-access-verify
```

Then record the final result in a dated release-candidate run record.

---

# Public Beta Decision

```text
Public beta: Blocked
Reason: Local production-style config, PostgreSQL, R2, hosted Cloud Run API health smoke, custom-domain API health smoke, hosted frontend/API custom-domain header smoke, unauthenticated browser-route/API protection checks, managed-identity login completion, authenticated project create/read/list smoke, hosted import processing, monitoring workflow status, hosted export creation, bounded hosted log review, smoke project cleanup, hosted audit integrity verification, hosted audit append-only access verification, provider config check, observability config check, and internal release-candidate signoff have passed. Public beta remains blocked by public-facing legal/trust/support publication, final provider review, final bounded hosted observability review, backup/restore/audit readiness, prompt-pack polish, and final public-beta approval.
Previously recorded smoke success remains: hosted import processing, monitoring workflow status, hosted export creation, bounded hosted log review, smoke project cleanup, and internal release-candidate signoff have passed.
Existing non-audit blockers remain: Public beta remains blocked by public-facing legal/trust/support publication, final provider review, final bounded hosted observability review, backup/restore/audit readiness, prompt-pack polish, and final public-beta approval.
```
