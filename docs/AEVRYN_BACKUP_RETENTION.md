# Aevryn Backup Retention

> Built by **Aetherra Labs**

Backup retention is a Phase 11 privacy and recovery contract.

Core rule:

```text
Backups are for recovery.
They are not hidden story storage.
```

---

# Current V2 Adapter State

Current V2 local adapters write active project, import, run, snapshot, export, and source-content state to local development storage.

The current local adapters do not implement a separate backup system.

When a story is deleted through Aevryn-owned active storage, Phase 11 deletion tests verify that scoped metadata and stored source bytes are removed from active local storage.

---

# Production Backup Requirement

Before public beta, production storage must define:

* which systems are backed up
* how long backups are retained
* who can access backups
* whether backups are encrypted
* how restore access is audited
* how deleted story data ages out of backups
* whether a deletion receipt can truthfully describe active-storage deletion and backup retention separately

Production backups must be encrypted at rest.

Production restore access must be restricted to authorized recovery operators.

Production restore operations must be auditable.

---

# Deletion And Backups

When a user deletes a story, Aevryn must remove story data from active Aevryn-owned storage.

If production backups retain deleted story data for a recovery window, the product must disclose:

* the maximum backup retention window
* that deleted data is unavailable in active product surfaces after deletion
* that deleted data can remain in encrypted backups until backup expiration
* that backups must not be used to recreate deleted stories except for authorized disaster recovery

The public product must never say deleted story data is gone from all systems instantly unless production backup architecture makes that technically true.

---

# Not Allowed

Backups must not become:

* a hidden support browsing surface
* a hidden manuscript archive
* a training dataset
* an analytics dataset
* a way to bypass user deletion
* a way to retain deleted stories indefinitely

---

# Public-Beta Wording Candidate

The selected public-beta wording candidate is recorded in `docs/AEVRYN_BACKUP_RETENTION_DECISION.md`.

Candidate posture:

```text
Deleted projects and stories are removed from active Aevryn-owned product storage.
Encrypted production backups may retain deleted data for up to 30 days.
Backups are used only for authorized disaster recovery and service restoration.
Backups are not used for AI training, analytics, support browsing, or product exploration.
```

This candidate must be verified against final production backup provider behavior before public beta.

---

# Public Beta Blocker

Public beta remains blocked until the deployment plan verifies production backup retention behavior and can truthfully publish it.

The minimum acceptable public-beta posture is:

```text
Deleted stories are removed from active Aevryn-owned storage.
Encrypted backups may retain deleted data for a disclosed recovery window.
Backups expire on a documented schedule.
Aetherra Labs does not use backups for training, analytics, or support browsing.
```

---

# Future Hardening

Future phases should add:

* deletion receipts
* account-level deletion
* restore drills
* backup access logs
* backup-retention CI/deployment checks
* production object-storage lifecycle policy tests
