# Aevryn Backup And Restore Runbook

> Built by **Aetherra Labs**

This runbook defines the provider-specific backup and restore procedure Aevryn
must verify before public beta.

It does not approve public beta.

It exists so restore testing is repeatable, privacy-preserving, and honest about
what the selected providers do and do not restore.

---

# Status

```text
Runbook: Backup and restore
Status: Selected for restore/audit drill execution
Public beta: Blocked
```

No public-beta restore drill has passed until a dated copy of
`docs/AEVRYN_RESTORE_AUDIT_DRILL_RECORD.md` is completed with passing results.

---

# Core Rule

```text
Recovery must restore service without weakening story privacy.
```

Recovery must not become hidden manuscript retention.

Backup and restore procedures must preserve:

* ownership boundaries
* deletion behavior
* private storage boundaries
* audit integrity
* metadata-only diagnostics

---

# Selected Providers For The Public-Beta Candidate

Database provider:

```text
Supabase managed PostgreSQL
```

Object storage provider:

```text
Cloudflare R2 private bucket
```

Audit storage provider:

```text
Managed PostgreSQL audit table through PostgresqlAuditLedger
```

The selected candidate does not use public buckets.

The frontend must not receive R2 credentials.

---

# Provider Facts To Verify

Supabase database backups:

* Paid Supabase projects have managed daily database backups.
* Daily backup retention depends on the Supabase plan.
* Point-in-Time Recovery is an add-on for finer-grained restore windows.
* Restoring a Supabase backup can make the project inaccessible during restore.
* Supabase database backups do not include Storage API objects.
* Daily backups do not store passwords for custom database roles, so custom role
  passwords may need to be reset after restore.

Cloudflare R2 object lifecycle:

* R2 lifecycle rules can expire objects by bucket or prefix.
* Lifecycle deletion is bucket-level object policy, not PostgreSQL restore.
* Objects are typically removed within 24 hours of the expiration value.
* Lifecycle configuration must be verified against the selected bucket before
  public deletion wording is finalized.

These provider facts must be checked against current provider documentation
again before public beta signoff.

---

# Required Public-Beta Backup Posture

The public-beta candidate remains:

```text
Encrypted production backups may retain deleted data for up to 30 days.
Backups are used only for authorized disaster recovery and service restoration.
Backups are not used for AI training, analytics, support browsing, or product exploration.
```

If the selected production provider cannot support that wording, update
`docs/AEVRYN_BACKUP_RETENTION_DECISION.md`, public trust copy, Privacy Policy,
support procedure, and release-candidate records before public beta.

---

# Restore Drill Environment

The restore drill must run in an isolated staging or release-candidate
environment.

The restored environment must not serve public production traffic.

Required isolation checks:

* separate frontend URL or no public frontend
* separate API URL or no public API route
* separate database target
* separate R2 bucket or prefix
* separate Supabase project if provider restore tooling requires it
* Cloud Run traffic remains pointed at the production service unless explicitly
  testing an isolated restore service

Do not restore directly over production for the public-beta drill unless the
project owner explicitly accepts downtime and risk in writing.

---

# Required Drill Data

Use synthetic or owner-approved content only.

The drill data must include:

* one restore-test user
* one project
* one active story
* one small imported source file
* one successful processing run
* one canon snapshot
* one generated export
* one disposable story deleted before the restore point is captured
* audit events covering creation, import, processing, snapshot, export, and
  deletion

Do not use unpublished third-party manuscripts as restore-drill evidence.

---

# Procedure

1. Create restore-test data in the source release-candidate environment.
2. Confirm active product deletion removes the disposable story from product
   surfaces.
3. Confirm import and export storage references remain private.
4. Confirm `aevryn audit-ledger-verify` passes before backup capture.
5. Capture or select the database restore point according to the Supabase backup
   process.
6. Capture the R2 object state needed for the isolated restore target, or verify
   that the selected restore process intentionally does not restore deleted R2
   objects.
7. Restore into an isolated staging or release-candidate target.
8. Reset custom database role passwords if the restore process requires it.
9. Reapply restricted runtime privileges using
   `docs/AEVRYN_RESTRICTED_DATABASE_ROLE_RUNBOOK.md` if restore changes role
   ownership or role credentials.
10. Point the isolated API at the restored database and isolated R2 target.
11. Run the hosted-production-style metadata checks against the isolated target.
12. Verify ownership boundaries.
13. Verify source storage references are owner-scoped.
14. Verify export access is owner-scoped.
15. Verify deleted story data does not reappear in active product surfaces.
16. Verify audit integrity after restore.
17. Review restore logs for metadata-only behavior.
18. Complete a dated copy of `docs/AEVRYN_RESTORE_AUDIT_DRILL_RECORD.md`.

---

# Required Commands

Run in an environment configured for the isolated restore target:

```powershell
python -m aevryn.cli production-config-check
python -m aevryn.cli audit-ledger-verify
python -m aevryn.cli audit-access-report
python -m aevryn.cli audit-access-verify
python -m aevryn.cli observability-config-check
```

Optional storage smoke for the isolated R2 target:

```powershell
python -m aevryn.cli storage-smoke
```

Do not run these commands against a database URL printed in the terminal or
copied into a document.

---

# Required Passing Evidence

The dated drill record must include:

```text
production_config_check=passed
audit_ledger_verify=passed
audit_access_verify=passed
observability_config_check=passed
source_storage_owner_scoped=passed
export_storage_owner_scoped=passed
deleted_story_absent_from_product_surfaces=passed
restore_logs_metadata_only=passed
operator_broad_manuscript_access_required=false
production_traffic_attached=false
```

The drill record must not include:

* database URLs
* passwords
* hostnames
* usernames
* storage references
* signed URLs
* full source prose
* full provider prompts
* full provider responses
* full generated exports

---

# Stop Conditions

Stop the drill and keep public beta blocked if:

* the restored environment can serve production users unintentionally
* deleted story data reappears in product surfaces
* cross-user access succeeds
* audit integrity fails
* audit access verification fails
* R2 objects are public or require public bucket access
* restore logs include source prose, credentials, tokens, private URLs,
  hostnames, usernames, or machine-local paths
* restore operators must browse full manuscripts to complete recovery
* custom database role passwords cannot be restored or reset safely

Any exposed secret must be rotated.

Any exposed private story content must be treated as a privacy incident.

---

# Acceptance

This runbook is accepted when the restore/audit drill passes in an isolated
environment and the dated drill record proves ownership, deletion, audit, and
metadata-only boundaries survived restore.
