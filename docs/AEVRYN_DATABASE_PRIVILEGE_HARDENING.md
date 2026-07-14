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

---

# Audit Table Target

The Cloud Run application database role must satisfy:

```text
audit_ledger_records SELECT: true
audit_ledger_records INSERT: true
audit_ledger_records UPDATE: false
audit_ledger_records DELETE: false
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

# Verification

Required verification after remediation:

* `aevryn production-config-check` passes without printing secrets
* `aevryn audit-ledger-verify` passes without printing secrets
* `aevryn audit-access-report` reports SELECT and INSERT as true
* `aevryn audit-access-report` reports UPDATE and DELETE as false
* `aevryn audit-access-verify` passes
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
