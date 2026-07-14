# Aevryn Restore Test Plan

> Built by **Aetherra Labs**

This document defines the restore drill Aevryn must pass before public beta.

---

# Purpose

Restore testing proves that Aevryn can recover from operational failure without turning recovery into hidden manuscript retention.

Core rule:

```text
Recovery must restore service without weakening story privacy.
```

---

# Scope

The restore drill covers:

* PostgreSQL project metadata
* Cloudflare R2 object references
* uploaded source-file references
* generated export references
* engine run and snapshot metadata
* audit-ledger metadata
* user/project/story ownership boundaries

The drill does not require restoring full public traffic.

It must run in a staging or release-candidate environment, not against production user data.

The required result template is defined in `docs/AEVRYN_RESTORE_AUDIT_DRILL_RECORD.md`.

---

# Privacy Boundary

Restore testing must not expose:

* full manuscripts
* full chapters
* full AI prompts
* full AI responses
* generated export content outside the authorized test
* credentials
* tokens
* private URLs
* hostnames
* usernames
* machine-local paths

Synthetic or owner-approved test projects should be used for restore drills.

Production user stories must not be copied into local development for convenience.

---

# Required Drill Data

The restore drill should create or use a dedicated test account with:

* one project
* one story
* one imported source file
* one processed run
* one canon snapshot
* one generated export
* one deletion event for a separate disposable story
* one audit-ledger chain containing workflow and deletion metadata

The disposable deleted story is used to verify deletion behavior after restore.

It must not contain real unpublished manuscript content.

---

# Restore Drill Steps

1. Create the dedicated restore-test account.
2. Create a project and story.
3. Upload a small synthetic source file.
4. Process the import.
5. Confirm snapshot availability.
6. Generate an export.
7. Create and delete a disposable story in the same project.
8. Confirm deleted active-storage data is unavailable.
9. Capture the backup or restore point according to the selected provider process.
10. Restore into an isolated staging or release-candidate environment.
11. Confirm the restored environment is not connected to production traffic.
12. Confirm project ownership boundaries still hold.
13. Confirm source and export storage references resolve only for the owner.
14. Confirm deleted active-storage data is not visible in product surfaces.
15. Confirm audit-ledger integrity checks pass.
16. Confirm restore logs and diagnostics are metadata-only.
17. Record the result in the release-candidate readiness record.
18. Copy `docs/AEVRYN_RESTORE_AUDIT_DRILL_RECORD.md` into a dated drill record and complete every result field.

---

# Required Assertions

The restore drill passes only when:

* restored projects remain scoped to the correct owner
* cross-user reads still fail closed
* source storage references remain private
* export download routes still enforce ownership
* deleted stories do not reappear in active product surfaces
* audit records remain metadata-only
* audit integrity can be verified after restore
* restore operators do not need broad manuscript browsing access
* restore logs do not print source prose or credentials
* the restored environment cannot accidentally serve production users

---

# Failure Handling

If restore testing fails:

* public beta remains blocked
* the failed assertion must be recorded
* any exposed secret must be rotated
* any exposed manuscript content must be treated as a privacy incident
* the backup or restore procedure must be corrected
* the restore drill must be rerun before signoff

---

# Acceptance

Restore readiness is accepted when:

```text
Aevryn can restore service in an isolated environment while preserving ownership, deletion, audit, and metadata-only privacy boundaries.
```
