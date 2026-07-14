# Aevryn Backup And Recovery

> Built by **Aetherra Labs**

Internal engineering contract for backup, restore, and disaster recovery.

---

# Core Rule

```text
Recovery must not become hidden retention.
```

---

# Backup Scope

Production backup planning must cover:

* account records
* project metadata
* story metadata
* source upload storage
* canon snapshots
* exports
* audit records
* configuration needed to restore service

Local development adapters do not define production backup behavior.

---

# Backup Frequency

Production deployment must select backup frequency based on recovery point objective.

Before public beta, Aetherra Labs must define:

* backup schedule
* recovery point objective
* recovery time objective
* backup retention window

The selected public-beta backup retention wording candidate is recorded in `docs/AEVRYN_BACKUP_RETENTION_DECISION.md`.

---

# Encryption

Production backups must be encrypted at rest.

Backup keys must be managed outside the application repository.

Restore operators must not receive broad secret access by default.

---

# Recovery Testing

Recovery must be tested before public beta.

Restore tests should verify:

* data integrity
* audit ledger integrity
* project/story ownership boundaries
* deleted story behavior
* no unexpected source-prose exposure in restore logs

---

# Disaster Recovery

Disaster recovery procedures must define:

* incident owner
* restore authority
* customer impact assessment
* communication steps
* rollback conditions
* post-recovery review

---

# Restore Validation

Restored environments must not silently become production.

Restore validation must confirm:

* environment separation
* secret rotation where needed
* access controls
* security headers
* API key configuration
* monitoring and audit behavior
