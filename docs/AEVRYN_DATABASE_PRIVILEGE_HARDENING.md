# Aevryn Database Privilege Hardening

> Built by **Aetherra Labs**

This document tracks the production database least-privilege posture required before public beta.

---

# Status

```text
Area: Database privilege hardening
Status: Started
Public beta: Blocked
```

The 2026-07-14 hosted audit gate verified that the audit table exists and the audit hash chain is valid.

The same gate also found that the currently configured database role can update and delete `audit_ledger_records`.

That is not acceptable for public beta.

---

# Core Rule

```text
The application may append audit records.
It must not rewrite audit history.
```

Audit records are append-only accountability records.

The production application role should have only the database privileges required for normal product operation.

Privileged database administration must be separate from normal Cloud Run application traffic.

Schema bootstrap and migrations must be separate from normal Cloud Run application traffic.

Production runtime must use:

```text
AEVRYN_PROJECT_DATABASE_BOOTSTRAP=false
```

This prevents the hosted API from relying on schema-creation or schema-alteration privileges during startup.

---

# Audit Table Target

The Cloud Run application database role must satisfy:

```text
audit_ledger_records SELECT: true
audit_ledger_records INSERT: true
audit_ledger_records UPDATE: false
audit_ledger_records DELETE: false
audit_ledger_records TRUNCATE: false
audit_ledger_records TABLE OWNER: false
```

The hosted release gate is:

```powershell
python -m aevryn.cli audit-access-verify
```

The diagnostic report is:

```powershell
python -m aevryn.cli audit-access-report
```

Both commands must print metadata only.

They must not print database URLs, credentials, role names, usernames, hostnames, audit rows, source prose, AI payloads, or storage references.

---

# Required Remediation

Before public beta, Aevryn must use one of these reviewed approaches:

* a restricted PostgreSQL application role for Cloud Run
* an equivalent managed database policy that denies audit UPDATE and DELETE
* a dedicated audit writer role separated from administrative database access

The selected approach must be recorded in this document or a dated production operations record.

The production secret used by Cloud Run must reference the restricted role after the role is created and tested.

Do not weaken `audit-access-verify` to pass a privileged role.

---

# Provisioning Procedure

This procedure must be performed with an administrative database connection and must not print credentials, database URLs, hostnames, usernames, or role names in logs.

Reviewed SQL template:

```text
docs/AEVRYN_POSTGRESQL_RUNTIME_PRIVILEGES.sql
```

Operational runbook:

```text
docs/AEVRYN_RESTRICTED_DATABASE_ROLE_RUNBOOK.md
```

1. Confirm the current schema exists and the hosted audit ledger verifies.
2. Create or update the restricted runtime database role through a reviewed migration or Supabase SQL editor session.
3. Grant the runtime role only the privileges required for normal application behavior.
4. Grant `SELECT` and `INSERT` on `audit_ledger_records`.
5. Revoke `UPDATE`, `DELETE`, and `TRUNCATE` on `audit_ledger_records`.
6. Ensure the runtime role does not own `audit_ledger_records`.
7. Revoke public table privileges on `audit_ledger_records`.
8. Grant sequence privileges only if the runtime role requires them for tables with sequences.
9. Update the production database URL secret to use the restricted runtime role.
10. Set `AEVRYN_PROJECT_DATABASE_BOOTSTRAP=false` in Cloud Run.
11. Redeploy Cloud Run.
12. Run the verification gates in this document.

The runtime role may read, insert, update, and delete normal product records where required by project workflows, project deletion, import processing, background jobs, snapshots, exports, and settings.

The runtime role must not update or delete audit history.

The runtime role must not truncate audit history.

The runtime role must not own the audit table.

Audit append serialization uses a transaction-scoped PostgreSQL advisory lock so audit writes do not require table-level update/delete privileges.

Migration/admin credentials must remain separate and must not be used by Cloud Run.

---

# Verification

Required verification after remediation:

* `aevryn production-config-check` passes without printing secrets
* `aevryn audit-ledger-verify` passes without printing secrets
* `aevryn audit-access-report` reports SELECT and INSERT as true
* `aevryn audit-access-report` reports UPDATE, DELETE, and TRUNCATE as false
* `aevryn audit-access-report` reports `is_table_owner=false`
* `aevryn audit-access-verify` passes
* `AEVRYN_PROJECT_DATABASE_BOOTSTRAP=false` is present in the hosted runtime configuration
* hosted API startup still succeeds
* hosted import processing still appends workflow audit events
* sampled hosted logs remain metadata-only

The result must be recorded in:

* `docs/AEVRYN_PRODUCTION_LIKE_SMOKE_RECORD.md`
* `docs/AEVRYN_RELEASE_CANDIDATE_RUN_RECORD.md`
* `docs/AEVRYN_PUBLIC_BETA_SETUP_CHECKLIST.md`

---

# Current Evidence

2026-07-14 hosted audit gate:

```text
audit-ledger-verify: passed
audit-access-report: passed
audit-access-verify: failed
reason: UPDATE privilege is present; DELETE privilege is also present in the report
```

No secrets or source content were printed.

---

# Acceptance

This hardening item is accepted when:

```text
Cloud Run uses a reviewed least-privilege PostgreSQL role, audit writes still work, audit history cannot be updated or deleted through the application role, and the hosted audit gates pass with metadata-only output.
```
