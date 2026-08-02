# Aevryn Backup Retention Decision

> Built by **Aetherra Labs**

This document records the public-beta backup retention wording candidate for Aevryn.

It does not approve public beta.

---

# Status

```text
Decision: Backup retention wording candidate
Status: Provider source rechecked - owner/legal wording review pending
Public beta: Blocked
```

This decision gives Aevryn a truthful public wording target before beta. It must still be verified against the final production backup provider, final production storage lifecycle, and legal review.

The dated owner/legal review packet is recorded in
`docs/AEVRYN_BACKUP_RETENTION_OWNER_REVIEW_2026_08_02.md`.

The production configuration verification path is recorded in
`docs/AEVRYN_BACKUP_RETENTION_PRODUCTION_VERIFICATION.md`.

---

# Core Rule

```text
Deletion removes active product data. Backups expire on a disclosed schedule.
```

Aevryn must never imply that deletion instantly removes data from every backup unless the production backup architecture makes that technically true.

---

# Selected Public-Beta Candidate

For public beta, Aevryn should publish this retention posture unless final production infrastructure requires a stricter window:

```text
Deleted projects and stories are removed from active Aevryn-owned product storage.
Encrypted production backups may retain deleted data for up to 30 days.
Backups are used only for authorized disaster recovery and service restoration.
Backups are not used for AI training, analytics, support browsing, or product exploration.
After backup expiration, deleted story data ages out of backup storage according to the documented backup lifecycle.
```

The 30-day window is a maximum public-beta candidate, not a minimum retention requirement.

If production backup tooling supports shorter retention safely, Aevryn may choose a shorter disclosed window before public beta.

---

# Provider Source Recheck

Official provider source review was rechecked on 2026-08-02.

Supabase managed PostgreSQL backup facts were rechecked against official Supabase backup documentation:

* daily database backup retention depends on plan
* Pro retention is 7 days
* Team retention is 14 days
* Enterprise retention is up to 30 days
* point-in-time recovery is a separate add-on
* database backups do not include Supabase Storage API objects

Cloudflare R2 object retention and deletion facts were rechecked against official Cloudflare R2 documentation:

* lifecycle rules can define object retention and expiration
* object deletion is irreversible
* lifecycle-managed expiration is typically processed within 24 hours of the configured expiration time
* lifecycle changes can take longer to affect existing objects

These source checks support the selected maximum-window candidate, but they do not complete owner/legal approval.

Production verification tooling now exists:

```powershell
python -m aevryn.cli backup-retention-config-check
```

The command verifies declared production Supabase plan/window metadata and R2
deletion/lifecycle metadata without printing secrets.

---

# Active Storage Deletion

Active-storage deletion means Aevryn removes scoped active product data owned by Aevryn systems, including:

* project and story metadata
* saved import metadata
* stored source bytes
* engine runs scoped to the deleted project or story
* canon snapshots scoped to the deleted project or story
* exports scoped to the deleted project or story
* queued or completed background job metadata scoped to the deleted project or story
* derived output records scoped to the deleted project or story

Active deletion must also keep logs, monitoring, support records, and audit records metadata-only.

---

# Backup Boundaries

Backups must:

* be encrypted at rest
* be access-limited to authorized recovery operators
* be used only for recovery and restore validation
* have restore operations logged or otherwise auditable where technically possible
* expire on a documented lifecycle schedule

Backups must not:

* become hidden manuscript storage
* become a support browsing tool
* become an analytics source
* become a training dataset
* be used to bypass a user's deletion decision outside authorized disaster recovery
* retain deleted stories indefinitely

---

# Restore Boundary

If a disaster recovery restore uses a backup that still contains data deleted after the restore point, Aetherra Labs must validate restored product state before allowing user access.

Restore validation must confirm:

* deleted active-storage data does not reappear in normal product surfaces unexpectedly
* story ownership boundaries remain intact
* restore logs remain metadata-only
* any reintroduced deleted data is handled under the documented recovery procedure

---

# Public Copy

Approved product-facing wording should be close to:

```text
When you delete a project or story, Aevryn removes it from active Aevryn-owned product storage. Encrypted production backups may retain deleted data for up to 30 days for authorized disaster recovery. Backups are not used for AI training, analytics, support browsing, or product exploration.
```

Legal-sensitive versions of this wording must be reviewed before public beta.

---

# Public Beta Blockers

Public beta remains blocked until:

* production Supabase plan retention is verified against the selected maximum window
* production R2 lifecycle/deletion policy is verified against the selected wording
* production backup encryption is verified
* restore access control is documented
* restore validation procedure is tested or explicitly accepted as a residual risk
* Privacy Policy, User Rights, Support, and Trust pages use consistent deletion wording
* legal-sensitive wording receives owner and attorney review

---

# Acceptance

This decision is accepted when:

```text
Aevryn can truthfully tell users what deletion removes immediately, what backups may retain temporarily, and what backups are never used for.
```
