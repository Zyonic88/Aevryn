# Aevryn Restore And Audit Drill Record

> Built by **Aetherra Labs**

This document is the required record template for the public-beta restore and audit drill.

It does not approve public beta.

It turns restore and audit readiness into a repeatable engineering test.

---

# Status

```text
Record type: Restore and audit drill record
Status: Template selected
Public beta: Blocked
```

No public-beta restore drill has passed until this record is copied into a dated run record and completed with passing results.

Provider-specific execution details live in
`docs/AEVRYN_BACKUP_RESTORE_RUNBOOK.md`.

---

# Core Rule

```text
Restore service without restoring private story exposure.
```

The drill must prove that recovery preserves ownership, deletion, audit integrity, and metadata-only diagnostics.

---

# Required Environment

The drill must run in an isolated staging or release-candidate environment.

The restored environment must not serve public production traffic.

Required environment record:

| Field | Value |
| --- | --- |
| Drill ID | `restore-audit-YYYY-MM-DD-001` |
| Date | `TBD` |
| Operator | `TBD` |
| Source environment | `TBD` |
| Restore target environment | `TBD` |
| Database provider | `TBD` |
| Object storage provider | `TBD` |
| Audit storage provider | `TBD` |
| Backup snapshot or restore point | `TBD` |
| Production traffic attached | `No` |

---

# Required Test Data

Use a dedicated restore-test account and synthetic or owner-approved content only.

Required data:

* one restore-test user
* one project
* one active story
* one small imported source file
* one successful processing run
* one canon snapshot
* one generated export
* one disposable story that is deleted before backup capture
* audit events for project creation, story creation, import saved, run submitted, worker result, snapshot creation, export generation, and disposable story deletion

Production user manuscripts must not be copied into local development or staging for convenience.

---

# Drill Steps

Each step must be marked `PASS`, `FAIL`, or `BLOCKED`.

| Step | Required Evidence | Result |
| --- | --- | --- |
| Create restore-test account | Account exists in source environment | `TBD` |
| Create project and active story | Project/story IDs recorded | `TBD` |
| Upload synthetic source | Source storage reference exists without public access | `TBD` |
| Process import | Run reaches succeeded state or recorded expected failure | `TBD` |
| Confirm snapshot | Snapshot metadata and availability recorded | `TBD` |
| Generate export | Export metadata recorded and access is owner-scoped | `TBD` |
| Create disposable story | Disposable story ID recorded | `TBD` |
| Delete disposable story | Active product surfaces no longer show it | `TBD` |
| Capture restore point | Backup or restore point ID recorded | `TBD` |
| Restore isolated target | Restored environment is separated from production traffic | `TBD` |
| Verify ownership boundaries | Cross-user project/story reads fail closed | `TBD` |
| Verify source references | Source bytes resolve only for the owner | `TBD` |
| Verify export references | Export access resolves only for the owner | `TBD` |
| Verify deleted story behavior | Deleted story does not reappear in active product surfaces | `TBD` |
| Verify audit chain | Audit integrity check passes after restore | `TBD` |
| Verify restore logs | Logs remain metadata-only | `TBD` |
| Verify operator access | Restore did not require broad manuscript browsing | `TBD` |

---

# Required Assertions

The drill passes only when all assertions are true:

* restored projects remain scoped to the correct owner
* cross-user reads fail closed
* source storage references remain private
* export download routes remain owner-scoped
* deleted stories do not reappear in active product surfaces
* audit ledger integrity verifies after restore
* audit records remain metadata-only
* restore logs do not include source prose
* restore logs do not include full AI provider payloads
* restore logs do not include credentials, tokens, private URLs, hostnames, usernames, or machine-local paths
* restore operators do not need broad manuscript browsing access
* restored environment cannot accidentally serve production users

---

# Stop Conditions

Stop the drill and treat it as failed if any of the following occur:

* full manuscript text appears in logs, screenshots, support notes, or drill evidence
* full provider prompts or responses appear in logs or drill evidence
* credentials, tokens, database URLs, provider keys, storage keys, or signed URLs are exposed
* deleted active-storage data reappears in product surfaces
* cross-user access succeeds
* audit integrity fails
* restored environment is connected to production traffic unintentionally

Any exposed secret must be rotated.

Any exposed private story content must be treated as a privacy incident.

---

# Result Record

```text
Restore drill result: NOT RUN
Audit integrity result: NOT RUN
Metadata-only log review result: NOT RUN
Deletion-after-restore result: NOT RUN
Public beta: BLOCKED
```

Final result must be one of:

* `passed`
* `failed`
* `blocked`

Public beta remains blocked unless the final result is `passed`.

---

# Acceptance

This drill record is accepted when:

```text
Aevryn has a dated restore/audit drill proving that service can be restored in an isolated environment without weakening ownership, deletion, audit integrity, or metadata-only privacy boundaries.
```
