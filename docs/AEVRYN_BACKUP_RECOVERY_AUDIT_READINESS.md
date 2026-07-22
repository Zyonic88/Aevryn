# Aevryn Backup, Recovery, And Audit Readiness

> Built by **Aetherra Labs**

This document tracks V2 Release Candidate Readiness Gate 5.

Gate 5 turns backup, restore, disaster recovery, and audit-ledger contracts into production decisions that can be tested before public beta.

---

# Status

```text
Gate: Backup, Recovery, And Audit
Status: Started
Public beta: Blocked
```

Aevryn has local deletion tests and audit-ledger architecture.

Public beta still needs production backup, restore, and audit-storage decisions.

---

# Core Rule

```text
Recovery must not become hidden retention.
```

Backups and audit records must help recover and explain the system without becoming hidden copies of user manuscripts.

---

# Source Contracts

Gate 5 builds on:

* `docs/AEVRYN_BACKUP_RETENTION.md`
* `docs/BACKUP_AND_RECOVERY.md`
* `docs/AEVRYN_AUDIT_LEDGER.md`
* `docs/AEVRYN_DATABASE_PRIVILEGE_HARDENING.md`
* `docs/DATA_RETENTION_POLICY.md`
* `docs/AEVRYN_RESTORE_TEST_PLAN.md`
* `docs/AEVRYN_RESTORE_AUDIT_DRILL_RECORD.md`
* `docs/AEVRYN_BACKUP_RESTORE_RUNBOOK.md`
* `docs/AEVRYN_RESTORE_AUDIT_DRILL_2026_07_17.md`

These documents define the privacy and engineering boundaries.

This readiness tracker records what still blocks public beta.

---

# Backup Decisions

Production backup planning must select:

* backed-up systems
* backup provider
* backup frequency
* recovery point objective
* recovery time objective
* backup retention window
* backup encryption approach
* backup key management
* restore operator access
* backup access logging
* deleted-story aging behavior

Backup retention must be explainable to users in plain language.

---

# Restore Testing

Before public beta, restore testing must prove:

* project ownership boundaries survive restore
* story ownership boundaries survive restore
* source upload references still resolve correctly
* deleted active-storage data is not recreated into product surfaces unexpectedly
* audit-ledger integrity survives restore
* restore logs remain metadata-only
* restored environments do not silently become production

Restore tests must not expose full manuscripts in logs, support artifacts, or screenshots.

The concrete restore drill is defined in `docs/AEVRYN_RESTORE_TEST_PLAN.md`.

The required result template is defined in `docs/AEVRYN_RESTORE_AUDIT_DRILL_RECORD.md`.

The provider-specific execution runbook is defined in
`docs/AEVRYN_BACKUP_RESTORE_RUNBOOK.md`.

---

# Disaster Recovery

Disaster recovery planning must define:

* incident owner
* restore authority
* rollback authority
* secret rotation triggers
* customer impact assessment
* user notification criteria
* provider outage handling
* post-recovery review process

Recovery procedures must preserve story privacy while allowing containment and service restoration.

---

# Audit Storage

Production audit planning must select:

* audit storage provider
* retention window
* access controls
* integrity verification process
* event ingestion path
* release-gate verification
* export or inspection process for authorized support

Audit records must remain append-only, tamper-evident, and metadata-only.

Audit storage must not contain full source prose, full AI responses, credentials, tokens, private URLs, hostnames, usernames, or machine-local paths.

The public-beta audit storage candidate is selected in `docs/AEVRYN_AUDIT_STORAGE_POLICY_DECISION.md`.

The selected candidate uses managed PostgreSQL audit tables owned by Aevryn's Project Database environment.

`PostgresqlAuditLedger` implements the selected storage adapter.

Core API and worker workflow events now append metadata-only audit records through
the configured audit writer.

---

# Audit Event Coverage

Public beta should capture security-relevant and workflow-relevant events, including:

* user registration
* login success and failure
* password reset request
* project creation
* project deletion
* story creation
* story deletion
* import saved
* run submitted
* worker drain completion
* snapshot created
* export generated
* settings changed
* security configuration failure
* cross-user access attempt

Deletion events must describe what was deleted without copying the deleted content.

---

# Deletion And Backup Disclosure

Before public beta, Aevryn must be able to truthfully explain:

* what active-storage deletion removes
* whether deleted story data can remain in encrypted backups
* maximum backup retention window
* whether backups can be restored after deletion
* who can access backups
* whether backup access is audited
* whether audit records remain after deletion

The public product must not promise instant deletion from every backup unless production architecture makes that true.

---

# Public Beta Blockers

Public beta remains blocked until:

* production backup frequency is selected
* backup retention window is selected
* backup encryption is verified
* restore test is completed
* disaster recovery procedure is documented
* production audit storage is selected
* audit retention is selected
* audit access controls are configured and reviewed through hosted audit access verification and reporting
* hosted audit integrity verification is recorded in the release gate
* deletion and backup language is aligned with production behavior

Current implementation progress:

```text
docs/AEVRYN_RESTORE_TEST_PLAN.md defines the restore drill, privacy boundary, required assertions, and failure handling.
docs/AEVRYN_RESTORE_AUDIT_DRILL_RECORD.md defines the repeatable restore/audit drill record and stop conditions.
docs/AEVRYN_BACKUP_RESTORE_RUNBOOK.md defines the selected Supabase PostgreSQL and Cloudflare R2 restore procedure, custom role password reset caveat, metadata-only commands, and stop conditions.
`aevryn restore-drill-verify` verifies restored API ownership, deletion, import, and export boundaries with metadata-only output against an isolated API target.
Public-beta backup retention wording candidate is selected in `docs/AEVRYN_BACKUP_RETENTION_DECISION.md`.
Public-beta audit storage policy candidate is selected in `docs/AEVRYN_AUDIT_STORAGE_POLICY_DECISION.md`.
`PostgresqlAuditLedger` implements the selected PostgreSQL adapter.
Core API and worker workflow events are wired to the configured audit writer.
Identity, password reset, project settings, and cross-user settings access-denial
events are wired to the configured audit writer.
Production configuration check failures are wired to the configured PostgreSQL
audit writer when audit storage can be constructed from the supplied deployment
settings.
`aevryn audit-ledger-verify` verifies the configured PostgreSQL audit ledger hash
chain without printing secrets.
`aevryn audit-access-report` reports configured PostgreSQL audit table and
privilege metadata without reading audit rows or printing secrets.
`aevryn audit-access-verify` fails closed unless the configured PostgreSQL audit
role can read and append audit records without update, delete, truncate, or
audit-table ownership privileges.
The hosted audit command sequence is:

```powershell
python -m aevryn.cli production-config-check
python -m aevryn.cli audit-ledger-verify
python -m aevryn.cli audit-access-report
python -m aevryn.cli audit-access-verify
```

The report command records metadata for review. The verify command owns the
gate decision and must not be bypassed or weakened to pass a privileged role.
The report includes `is_table_owner` as a boolean and must report
`is_table_owner=false` before public beta.
Hosted `aevryn audit-ledger-verify` passed with metadata-only output on
2026-07-14. Hosted `aevryn audit-access-report` passed with metadata-only
output, but hosted `aevryn audit-access-verify` failed because the current
database role has UPDATE and DELETE privileges on `audit_ledger_records`.
The restricted runtime role remediation runbook is
`docs/AEVRYN_RESTRICTED_DATABASE_ROLE_RUNBOOK.md`.
On 2026-07-17, Cloud Run was moved to a restricted runtime PostgreSQL role.
Hosted `aevryn audit-ledger-verify`, `aevryn audit-access-report`, and
`aevryn audit-access-verify` passed with metadata-only output. The report showed
`can_update=false`, `can_delete=false`, `can_truncate=false`, and
`is_table_owner=false`.

Production backup provider verification runbook is selected. Restore execution, audit retention enforcement, and dated restore/audit drill completion remain open.
The 2026-07-17 source-environment restore preflight passed production config,
audit integrity, restricted audit access, observability config, and R2 storage
smoke with metadata-only output. The 2026-07-17 hosted source fixture also
created synthetic project/story/import/run/snapshot/export evidence and deleted a
disposable story before restore-point capture. A source restore-point candidate
timestamp was recorded after post-fixture audit and R2 checks passed. The
Supabase backup/PITR point has not been selected, and the isolated Aevryn
restore runtime has not been created, pointed at the restored database, or
verified.
The restored Supabase project `aevryn-restore-drill-2026-07-22` exists with
project ref `zemkfcbijtauvvencxyy`, differs from production ref
`xmttttbygokqbmwtucgi`, and is not attached to the production Cloud Run API.
On 2026-07-22, restored database audit verification passed through a restricted
runtime PostgreSQL role. The restored audit access report and verify commands
reported `can_update=false`, `can_delete=false`, `can_truncate=false`, and
`is_table_owner=false`; restored audit ledger verification reported
`records_verified=5195`. Restore drill completion remains blocked until an
isolated Aevryn API target verifies ownership boundaries, source/export
owner-scoped access, deleted-story behavior, and metadata-only restore logs.
```

---

# Acceptance

Gate 5 is accepted when:

```text
Deleted stories are removed from active storage, backup retention is disclosed, restore behavior is tested, and audit records remain metadata-only and tamper-evident.
```
