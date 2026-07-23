# Aevryn Restricted Database Role Runbook

> Built by **Aetherra Labs**

This runbook defines the operational procedure for moving the hosted Aevryn API
from an administrative PostgreSQL connection to a restricted runtime database
role.

This runbook must not contain real database URLs, passwords, hostnames,
usernames, Supabase project secrets, or Cloud Run secret values.

---

# Purpose

Aevryn's production runtime must be able to operate the product without being
able to rewrite audit history.

The runtime database role may append audit records.

The runtime database role must not update, delete, truncate, or own audit
records.

---

# Core Rule

```text
Storage owns bytes. Database owns references. Engine owns meaning.
The application may append audit records.
The application must not rewrite audit history.
```

---

# Preconditions

Before using this runbook:

* `audit_ledger_records` already exists.
* Hosted `aevryn audit-ledger-verify` has passed.
* Cloud Run is configured with `AEVRYN_PROJECT_DATABASE_ADAPTER=postgresql`.
* Cloud Run is configured with `AEVRYN_PROJECT_DATABASE_BOOTSTRAP=false`.
* The operator has a privileged database connection for role provisioning.
* The operator has access to Google Secret Manager for
  `AEVRYN_PROJECT_DATABASE_URL`.

Stop if schema bootstrap or migrations are still being performed by the Cloud
Run runtime role.

---

# Step 1 - Create A Reviewed Execution Copy

Use this template:

```text
docs/AEVRYN_POSTGRESQL_RUNTIME_PRIVILEGES.sql
```

Create a temporary execution copy outside the repository.

Replace only:

```text
<runtime_role>
<migration_owner>
```

The runtime role is the login role used by Cloud Run.

The migration owner is an administrative or migration role that is not used by
Cloud Run.

Do not commit the rendered execution copy.

Do not paste the rendered execution copy into chat, issues, pull requests, or
public logs.

---

# Step 2 - Provision The Runtime Role

Create the runtime role through a privileged Supabase SQL session or an approved
database administration path.

Use a strong generated password.

Do not use the Supabase service role key as the PostgreSQL runtime password.

Do not use the administrative `postgres` connection string in Cloud Run.

If role creation is blocked by the provider, stop and record the blocker. Do not
work around this by using an administrative database URL in Cloud Run.

---

# Step 3 - Apply Runtime Privileges

Run the reviewed execution copy from Step 1 with the privileged database
connection.

The intended result is:

```text
normal product tables: read/write access required by product workflows
audit_ledger_records SELECT: true
audit_ledger_records INSERT: true
audit_ledger_records UPDATE: false
audit_ledger_records DELETE: false
audit_ledger_records TRUNCATE: false
audit_ledger_records TABLE OWNER: false
```

The runtime role must not own `audit_ledger_records`.

`PUBLIC` must not have table privileges on `audit_ledger_records`.

---

# Step 4 - Update Secret Manager

Update the existing Google Secret Manager secret:

```text
AEVRYN_PROJECT_DATABASE_URL
```

The new value must use the restricted runtime database role.

Do not paste the database URL into a repository file, issue, pull request,
browser screenshot, or chat.

PowerShell pattern:

```powershell
$env:AEVRYN_RESTRICTED_DATABASE_URL = "postgresql://<runtime_role>:<password>@<host>:5432/<database>?sslmode=require"
Write-Output $env:AEVRYN_RESTRICTED_DATABASE_URL | & "C:\Users\enigm\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd" secrets versions add AEVRYN_PROJECT_DATABASE_URL --data-file=-
Remove-Item Env:\AEVRYN_RESTRICTED_DATABASE_URL
```

Replace the placeholder value locally before running the command.

Do not paste the populated command into chat.

---

# Step 5 - Roll Cloud Run

Create a new Cloud Run revision so the hosted service reads the latest secret
version.

PowerShell:

```powershell
& "C:\Users\enigm\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd" run services update aevryn-api `
  --region us-central1 `
  --update-env-vars AEVRYN_PROJECT_DATABASE_BOOTSTRAP=false
```

Do not switch `AEVRYN_PROJECT_DATABASE_BOOTSTRAP` back to true in production.

---

# Step 6 - Verify Metadata-Only Gates

Run the hosted-production environment checks from a local shell configured with
the hosted production-like environment.

Do not print the database URL.

Required commands:

```powershell
$env:PYTHONPATH = "src"
python -m aevryn.cli production-config-check
python -m aevryn.cli audit-ledger-verify
python -m aevryn.cli audit-access-report
python -m aevryn.cli audit-access-verify
```

Expected audit access result:

```text
table_exists=true
can_select=true
can_insert=true
can_update=false
can_delete=false
can_truncate=false
is_table_owner=false
ok=audit_access_append_only_verified
secrets_printed=0
```

If `audit-access-verify` fails, stop. Do not weaken the command or tests.

---

# Step 7 - Hosted API Smoke

After the database role verifies, check the hosted API health endpoint:

```powershell
curl.exe -i https://api.aevryn.ai/v2/health
```

Expected result:

```text
HTTP 200
status=ok
project_storage=configured
import_content_storage=configured
```

Then run one hosted authenticated workflow smoke before signoff:

* login through the managed identity provider
* create a project
* inspect and save an import
* process the import
* confirm workflow events are visible as metadata
* confirm the audit gate still passes

No source prose, credentials, storage URLs, or full AI payloads may appear in
logs or copied output.

---

# Evidence To Record

Record only metadata in:

* `docs/AEVRYN_DATABASE_PRIVILEGE_HARDENING.md`
* `docs/AEVRYN_PRODUCTION_LIKE_SMOKE_RECORD.md`
* `docs/AEVRYN_RELEASE_CANDIDATE_RUN_RECORD.md`
* `docs/AEVRYN_PUBLIC_BETA_SETUP_CHECKLIST.md`

Record:

```text
date
operator
Cloud Run service
database role posture passed or failed
audit-ledger-verify result
audit-access-report result summary
audit-access-verify result
hosted API health result
notes and blockers
```

Do not record:

```text
database URLs
passwords
hostnames
usernames
tokens
storage references
uploaded source text
full AI request or response payloads
```

---

# Stop Conditions

Stop and do not mark the gate complete if:

* Cloud Run still uses an administrative database URL.
* `AEVRYN_PROJECT_DATABASE_BOOTSTRAP=false` is missing.
* `audit-access-report` reports `can_update=true`.
* `audit-access-report` reports `can_delete=true`.
* `audit-access-report` reports `can_truncate=true`.
* `audit-access-report` reports `is_table_owner=true`.
* `audit-access-verify` fails.
* hosted API startup fails after the secret rotation.
* logs expose credentials, source prose, storage references, or full AI payloads.

---

# Acceptance

This runbook is accepted when Cloud Run uses the restricted PostgreSQL runtime
role, the hosted API still functions, and `aevryn audit-access-verify` passes
with metadata-only output.
