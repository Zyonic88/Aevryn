# Aevryn Restore And Audit Drill Record - 2026-07-17

> Built by **Aetherra Labs**

This is a dated restore/audit drill record for V2 public-beta readiness.

This record does not approve public beta.

This record does not claim a full restore drill passed.

It records that source-environment restore preflight checks passed, source-side
synthetic fixture data was created through the hosted API boundary, and that the
isolated restore target has not yet been created or verified.

---

# Status

```text
Record type: Restore and audit drill record
Drill ID: restore-audit-2026-07-17-001
Status: Source preflight passed; restore target not run
Source fixture: Passed
Public beta: Blocked
Final result: blocked
```

Public beta remains blocked until this drill is rerun or continued against an
isolated restore target and every required restore assertion passes.

---

# Core Rule

```text
Restore service without restoring private story exposure.
```

The drill must prove that recovery preserves ownership, deletion, audit
integrity, and metadata-only diagnostics.

---

# Environment Record

| Field | Value |
| --- | --- |
| Drill ID | `restore-audit-2026-07-17-001` |
| Date | `2026-07-17` |
| Operator | `Aetherra Labs project owner with Codex assistance` |
| Source environment | `Hosted production-like Aevryn environment` |
| Restore target environment | `Supabase project aevryn-restore-drill-2026-07-22` |
| Database provider | `Supabase managed PostgreSQL` |
| Object storage provider | `Cloudflare R2 private bucket` |
| Audit storage provider | `Managed PostgreSQL audit table through PostgresqlAuditLedger` |
| Backup snapshot or restore point | `Source restore-point candidate recorded; Supabase backup/PITR point not selected` |
| Production traffic attached | `No` |

---

# Source Preflight Commands

The following metadata-only commands were run against the hosted
production-like source environment:

```powershell
python -m aevryn.cli production-config-check
python -m aevryn.cli audit-ledger-verify
python -m aevryn.cli audit-access-report
python -m aevryn.cli audit-access-verify
python -m aevryn.cli observability-config-check
python -m aevryn.cli storage-smoke
```

No database URL, database credential, storage key, API key, Supabase key, OpenAI
key, session secret, worker key, source prose, full provider prompt, full
provider response, storage reference, private URL, hostname, username, or audit
row payload was printed.

---

# Source Preflight Results

```text
production_config_check=passed
startup_contract=ready
production_config_secrets_printed=0

audit_ledger_verify=passed
records_verified=1375
audit_ledger_verify_secrets_printed=0

audit_access_report=passed
table_exists=true
can_select=true
can_insert=true
can_update=false
can_delete=false
can_truncate=false
is_table_owner=false
audit_access_report_secrets_printed=0

audit_access_verify=passed
audit_access_verify_secrets_printed=0

observability_config_check=passed
log_destination=hosted
monitoring_destination=hosted
log_retention_days=30
monitoring_retention_days=30
security_alerts_enabled=true
metadata_only_logging=true
observability_config_secrets_printed=0

storage_smoke=passed
storage_provider=r2
objects_created=1
objects_deleted=1
```

---

# Source Fixture Results

The following metadata-only source fixture was created through the hosted API
boundary after the source preflight passed:

```text
drill_fixture=source
project_id=restore_drill_project_1acd3f86bd984a258fc04c976642131d
active_story_id=restore_drill_story_1acd3f86bd984a258fc04c976642131d
disposable_story_id=restore_drill_disposable_1acd3f86bd984a258fc04c976642131d
import_id=restore_drill_import_1acd3f86bd984a258fc04c976642131d
run_id=restore_drill_run_1acd3f86bd984a258fc04c976642131d
project_created=True
active_story_created=True
disposable_story_deleted=True
import_saved=True
run_submitted=True
worker_drained=True
worker_succeeded_jobs=1
run_status=succeeded
snapshots_available=True
export_created=True
inspect_chapters=1
inspect_scenes=1
inspect_evidence_anchors=2
saved_import_chapters=1
saved_import_scenes=1
source_bytes_printed=0
secrets_printed=0
restore_target_created=False
public_beta=blocked_until_isolated_restore_drill_passes
ok=restore_drill_fixture_prepared
```

The fixture used synthetic content only. The drill evidence did not print bearer
tokens, source prose, storage references, private URLs, provider prompts,
provider responses, or generated export bodies.

---

# Restore-Point Capture Candidate

After the source fixture passed, the following metadata-only source checks were
run to mark the source environment as ready for restore-point selection:

```text
source_restore_point_candidate_utc=2026-07-17T02:27:13Z

audit_ledger_verify=passed
records_verified=1413
audit_ledger_verify_secrets_printed=0

audit_access_report=passed
table_exists=true
can_select=true
can_insert=true
can_update=false
can_delete=false
can_truncate=false
is_table_owner=false
audit_access_report_secrets_printed=0

audit_access_verify=passed
audit_access_verify_secrets_printed=0

source_r2_storage_smoke=passed
storage_provider=r2
storage_bucket=aevryn-dev
storage_smoke_objects_created=1
storage_smoke_objects_deleted=1
```

This is not a completed database backup selection. The Supabase backup or PITR
restore point must still be selected through the provider restore flow, and the
restore must target an isolated project or environment before Gate 5 can pass.

---

# Restore Target Isolation Check

The restored Supabase project was created and reported healthy by the project
owner:

```text
restore_project_name=aevryn-restore-drill-2026-07-22
restore_supabase_url=https://zemkfcbijtauvvencxyy.supabase.co
restore_project_ref=zemkfcbijtauvvencxyy
restore_region=us-west-2
restore_status=healthy
production_project_ref=xmttttbygokqbmwtucgi
```

Initial isolation checks:

```text
restore_project_ref_differs_from_production=true
production_cloud_run_supabase_url=https://xmttttbygokqbmwtucgi.supabase.co
production_cloud_run_points_to_restore_project=false
cloud_run_services_in_us_central1=1
cloud_run_restore_service_exists=false
production_traffic_attached=false
```

This confirms the restore Supabase project is a distinct project and is not
currently attached to the production Cloud Run API. The restored database has
not yet been verified by Aevryn CLI checks, and no isolated API has been pointed
at the restored target.

---

# Drill Step Results

| Step | Required Evidence | Result |
| --- | --- | --- |
| Create restore-test account | Account exists in source environment | `PASSED - dedicated restore-drill auth user created` |
| Create project and active story | Project/story IDs recorded | `PASSED - synthetic project and active story IDs recorded` |
| Upload synthetic source | Source storage reference exists without public access | `PASSED - synthetic import saved without printing source bytes or storage refs` |
| Process import | Run reaches succeeded state or recorded expected failure | `PASSED - run_status=succeeded` |
| Confirm snapshot | Snapshot metadata and availability recorded | `PASSED - snapshots_available=True` |
| Generate export | Export metadata recorded and access is owner-scoped | `PASSED - export_created=True` |
| Create disposable story | Disposable story ID recorded | `PASSED - disposable story ID recorded` |
| Delete disposable story | Active product surfaces no longer show it | `PASSED - disposable story deleted before restore-point capture` |
| Capture restore point | Backup or restore point ID recorded | `PARTIAL - source restore-point candidate recorded; Supabase backup/PITR point not selected` |
| Restore isolated target | Restored environment is separated from production traffic | `PARTIAL - restored Supabase project exists and is not attached to production Cloud Run` |
| Verify ownership boundaries | Cross-user project/story reads fail closed | `BLOCKED - restore target not created` |
| Verify source references | Source bytes resolve only for the owner | `BLOCKED - restore target not created` |
| Verify export references | Export access resolves only for the owner | `BLOCKED - restore target not created` |
| Verify deleted story behavior | Deleted story does not reappear in active product surfaces | `BLOCKED - restore target not created` |
| Verify audit chain | Audit integrity check passes after restore | `BLOCKED - restore target not created` |
| Verify restore logs | Logs remain metadata-only | `BLOCKED - restore target not created` |
| Verify operator access | Restore did not require broad manuscript browsing | `BLOCKED - restore target not created` |

---

# Required Assertions

```text
restored_projects_scoped_to_owner=not_run
cross_user_reads_fail_closed=not_run
source_storage_references_private=not_run
export_downloads_owner_scoped=not_run
deleted_story_absent_from_product_surfaces=not_run
audit_ledger_integrity_after_restore=not_run
audit_records_metadata_only=passed_for_source_preflight
restore_logs_no_source_prose=not_run
restore_logs_no_full_provider_payloads=not_run
restore_logs_no_credentials_or_private_urls=not_run
operator_broad_manuscript_access_required=not_run
production_traffic_attached=false
```

---

# Result Record

```text
Restore drill result: BLOCKED
Audit integrity result: SOURCE PREFLIGHT PASSED
Metadata-only log review result: SOURCE PREFLIGHT PASSED FOR CLI OUTPUT
Source fixture result: PASSED
Deletion-after-restore result: NOT RUN
Public beta: BLOCKED
```

Final result:

```text
blocked
```

Reason:

```text
The source environment preflight and source fixture passed, but no isolated
restore target has been created, restored, or verified. This record cannot close
Gate 5.
```

---

# Next Required Action

Create an isolated restore target and continue the drill using
`docs/AEVRYN_BACKUP_RESTORE_RUNBOOK.md`.

The next run must verify:

* restored ownership boundaries
* cross-user access denial
* source and export owner-scoped access
* deleted-story absence from active product surfaces
* audit integrity after restore
* metadata-only restore logs
* no broad manuscript browsing by restore operators

---

# Acceptance

This dated record is accepted only as source-environment preflight evidence.

It is not accepted as a completed restore/audit drill.
