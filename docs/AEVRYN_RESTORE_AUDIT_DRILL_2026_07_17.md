# Aevryn Restore And Audit Drill Record - 2026-07-17

> Built by **Aetherra Labs**

This is a dated restore/audit drill record for V2 public-beta readiness.

This record claims only the restore/audit drill result. It does not approve
public beta.

It records that source-environment restore preflight checks passed, source-side
synthetic fixture data was created through the hosted API boundary, the isolated
restore target database passed audit verification, the isolated restore API
preserved ownership/deletion/storage boundaries, and the bounded hosted restore
log review remained metadata-only.

---

# Status

```text
Record type: Restore and audit drill record
Drill ID: restore-audit-2026-07-17-001
Status: Restore/audit drill passed
Source fixture: Passed
Public beta: Blocked
Final result: passed
```

Public beta remains blocked by other release gates and final owner approval.

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
cloud_run_restore_service_exists=true
cloud_run_restore_service_name=aevryn-api-restore
cloud_run_restore_public_access=false
restore_api_authenticated_health=passed
restore_api_unauthenticated_health_denied=passed
restore_api_config_check=passed
restore_api_config_execution=aevryn-restore-config-check-pgz2r
restore_api_config_ok=restore_api_config_contract_checked
restore_api_config_secrets_printed=0
production_traffic_attached=false
```

This confirms the restore Supabase project is a distinct project and is not
currently attached to the production Cloud Run API. A private Cloud Run restore
API target was deployed as `aevryn-api-restore`; authenticated `/v2/health`
returned `ok`, unauthenticated `/v2/health` returned 403, and the Cloud Run job
`aevryn-restore-config-check-pgz2r` reported
`ok=restore_api_config_contract_checked` with `secrets_printed=0`. The restored
database was also verified through Aevryn CLI audit checks using a restricted
runtime role.

---

# Restored Database Audit Verification

After the restored Supabase project was created and isolated from production
traffic, the restored database runtime role was reset and constrained so the
audit ledger remained append-only for the application runtime. The following
metadata-only checks passed against the restored database:

```text
restore_database_audit_access_report=passed
table_exists=true
can_select=true
can_insert=true
can_update=false
can_delete=false
can_truncate=false
is_table_owner=false
audit_access_report_secrets_printed=0

restore_database_audit_access_verify=passed
audit_access_verify_secrets_printed=0

restore_database_audit_ledger_verify=passed
records_verified=5195
audit_ledger_verify_secrets_printed=0
```

The commands used the restored database URL from process environment only. No
database URL, password, source prose, full provider payload, or audit row
payload was recorded in this document.

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
| Capture restore point | Backup or restore point ID recorded | `PASSED WITH LIMITATION - restored Supabase project name/ref recorded; provider restore-point ID not available in this record` |
| Restore isolated target | Restored environment is separated from production traffic | `PARTIAL - restored Supabase project exists, private restore API exists, config preflight passed, and no production Cloud Run traffic is attached` |
| Verify ownership boundaries | Cross-user project/story reads fail closed | `PASSED - restore API boundary verifier denied cross-user project/story/import/export access` |
| Verify source references | Source bytes resolve only for the owner | `PASSED - restore API boundary verifier confirmed owner-scoped import metadata and denied cross-user source access` |
| Verify export references | Export access resolves only for the owner | `PASSED - restore API boundary verifier confirmed owner export metadata/download and denied cross-user export access` |
| Verify deleted story behavior | Deleted story does not reappear in active product surfaces | `PASSED - restore API boundary verifier confirmed deleted story absence` |
| Verify audit chain | Audit integrity check passes after restore | `PASSED - restored database audit ledger verified 5195 records` |
| Verify restore logs | Logs remain metadata-only | `PASSED - bounded hosted restore service/job log review found metadata-only route and config output` |
| Verify operator access | Restore did not require broad manuscript browsing | `PARTIAL - private service deployed and checked without broad manuscript browsing` |

---

# Required Assertions

```text
restored_projects_scoped_to_owner=passed
cross_user_reads_fail_closed=passed
source_storage_references_private=passed
export_downloads_owner_scoped=passed
deleted_story_absent_from_product_surfaces=passed
audit_ledger_integrity_after_restore=passed
restored_audit_records_verified=5195
restore_api_config_check=passed
restore_api_authenticated_health=passed
restore_api_unauthenticated_health_denied=passed
audit_records_metadata_only=passed_for_source_preflight_and_restored_database_cli_output
restore_logs_no_source_prose=passed
restore_logs_no_full_provider_payloads=passed
restore_logs_no_credentials_or_private_urls=passed
restore_logs_metadata_only=passed
operator_broad_manuscript_access_required=false
production_traffic_attached=false
restore_drill_api_boundaries_verified=passed
```

---

# Result Record

```text
Restore drill result: PASSED
Audit integrity result: SOURCE PREFLIGHT AND RESTORED DATABASE AUDIT VERIFY PASSED
Metadata-only log review result: SOURCE PREFLIGHT, RESTORED DATABASE CLI OUTPUT, AND BOUNDED HOSTED RESTORE LOG REVIEW PASSED
Source fixture result: PASSED
Restore API boundary result: PASSED
Deletion-after-restore result: PASSED THROUGH ISOLATED API
Public beta: BLOCKED BY OTHER RELEASE GATES AND FINAL OWNER APPROVAL
```

Final result:

```text
passed
```

Reason:

```text
The source environment preflight, source fixture, restored target isolation,
restored database audit verification, private restore API deployment, restore
API config preflight, isolated restore API boundary verification, and bounded
hosted restore log review passed. The drill did not require broad manuscript
browsing by restore operators. This record closes the restore/audit drill gate,
but it does not approve public beta by itself.
```

---

# Hosted Restore Log Review

Environment:

```text
Execution surface: Google Cloud Run bounded service/job log samples
Service: aevryn-api-restore
Job: aevryn-restore-config-check
Region: us-central1
Service sample window: 2026-07-22 23:20:22 UTC through 2026-07-23 01:33:41 UTC
Job sample window: 2026-07-22 23:26:21 UTC
Service sampled lines: 47
Job sampled lines: 11
Status: Passed with metadata-only route/config finding
```

Observed metadata:

```text
Restore service logs included HTTP methods, HTTP statuses, project IDs, story
IDs, export IDs, route paths, and Google-managed proxy addresses.
Restore config job logs included environment/config readiness metadata and
secrets_printed=0.
```

Prohibited data checks:

```text
restore_logs_no_source_prose=passed
restore_logs_no_full_provider_payloads=passed
restore_logs_no_credentials_or_private_urls=passed
restore_logs_no_storage_refs_or_signed_urls=passed
restore_logs_no_user_email_addresses=passed
restore_logs_no_machine_local_paths=passed
restore_logs_metadata_only=passed
```

Finding:

```text
Cloud Run request logs include route-level restore workflow metadata. This is
acceptable for the restore drill because it is metadata-only and does not expose
source prose, full AI payloads, credentials, tokens, database URLs, storage
references, signed URLs, private bucket names, user emails, or machine-local
paths.
```

---

# Next Required Action

Continue non-restore public-beta blockers using the release readiness docs.

The next release-readiness work must verify:

* final public-facing legal/trust/support owner review
* final AI provider data-use review
* final public-beta approval checklist

The restored API boundary verification command passed:

```text
drill_verification=isolated_api
project_id=restore_drill_project_1acd3f86bd984a258fc04c976642131d
owner_project_read=passed
owner_active_story_present=passed
deleted_story_absent_from_product_surfaces=passed
owner_import_metadata_visible=passed
source_storage_owner_scoped=passed
project_status=succeeded
snapshots_available=true
owner_export_metadata_visible=passed
owner_export_download_available=passed
export_storage_owner_scoped=passed
cross_user_project_read=denied
cross_user_story_imports=denied
cross_user_exports=denied
cross_user_export_download=denied
deleted_story_imports=denied
private_cloud_run_auth=present
source_bytes_printed=0
export_bytes_printed=0
storage_refs_printed=0
secrets_printed=0
restore_logs_metadata_only=passed
production_traffic_attached=false
public_beta=blocked_by_other_release_gates_and_final_owner_approval
ok=restore_drill_api_boundaries_verified
```

The restore API config preflight must report
`ok=restore_api_config_contract_checked` and `production_traffic_attached=false`
before the boundary verifier can count toward Gate 5.

---

# Acceptance

This dated record is accepted as source-environment preflight evidence, restored
database audit evidence, restore API configuration evidence, isolated restore
API boundary evidence, and hosted restore log-review evidence.

This dated restore/audit drill is accepted as complete for the restore/audit
gate. It does not approve public beta by itself.
