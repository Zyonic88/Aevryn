# Aevryn Backup Retention Decision

> Built by **Aetherra Labs**

This document records the public-beta backup retention wording candidate for Aevryn.

It does not approve public beta.

---

# Status

```text
Decision: Backup retention wording candidate
Status: Selected for owner/legal review
Public beta: Blocked
```

This decision gives Aevryn a truthful public wording target before beta. It must still be verified against the final production backup provider, restore process, and legal review.

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

* production backup provider behavior supports the selected window
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
