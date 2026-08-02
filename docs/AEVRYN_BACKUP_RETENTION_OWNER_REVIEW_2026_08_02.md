# Aevryn Backup Retention Owner Review

> Built by **Aetherra Labs**

This worksheet records the backup-retention source recheck and owner/legal
review packet for Aevryn V2 public beta.

It is not legal advice.

It does not approve public beta.

---

# Status

```text
Review: Backup retention owner/legal review
Date: 2026-08-02
Status: Provider source rechecked - production verification tooling implemented; owner/legal wording review pending
Public beta: Blocked
```

---

# Core Rule

```text
Deletion removes active product data. Backups expire on a disclosed schedule.
```

Aevryn must tell users what is removed immediately, what may remain
temporarily in encrypted recovery backups, and what backups are never used for.

---

# Candidate Public Wording

```text
When you delete a project or story, Aevryn removes it from active
Aevryn-owned product storage. Encrypted production backups may retain deleted
data for up to 30 days for authorized disaster recovery. Backups are not used
for AI training, analytics, support browsing, or product exploration.
```

This is a maximum-window candidate, not a promise that every backup copy exists
for 30 days.

If the final production database or object-storage lifecycle supports a shorter
truthful retention window, Aevryn may disclose the shorter window before public
beta.

---

# Provider Source Recheck

Official provider source review was rechecked on 2026-08-02.

## Supabase Managed PostgreSQL

Source: https://supabase.com/docs/guides/platform/backups

Relevant source facts:

* Pro, Team, and Enterprise projects receive daily database backups.
* Daily backup retention depends on plan: Pro 7 days, Team 14 days, and
  Enterprise up to 30 days.
* Point-in-time recovery is a separate add-on with selectable retention
  windows.
* A restore operation may make the project inaccessible while the restore is
  running.
* Daily database backups do not include passwords for custom roles; custom role
  passwords may need to be reset after restore.
* Database backups do not include Supabase Storage API objects.

Owner verification still required:

```text
production_supabase_plan_retention=blocked_pending_owner_verification
```

## Cloudflare R2

Sources:

* https://developers.cloudflare.com/r2/buckets/object-lifecycles/
* https://developers.cloudflare.com/r2/objects/delete-objects/

Relevant source facts:

* R2 lifecycle rules can define object retention and expiration.
* Object deletion through supported R2 tools is irreversible.
* Lifecycle-managed object expiration is typically processed within 24 hours of
  the configured expiration time, with possible delays after lifecycle changes.
* Lifecycle configuration is bucket-level and requires storage write
  permission.

Owner verification still required:

```text
production_r2_lifecycle_policy=blocked_pending_owner_verification
```

Production verification tooling is recorded in:

* `docs/AEVRYN_BACKUP_RETENTION_PRODUCTION_VERIFICATION.md`

Run:

```powershell
python -m aevryn.cli backup-retention-config-check
```

The command validates the declared production Supabase plan/window and R2
deletion/lifecycle policy without printing secrets, database URLs, R2
credentials, bucket object names, source prose, or storage references.

---

# Verified Aevryn Evidence

The following Aevryn-controlled evidence has already passed:

* isolated restore drill passed
* deleted story absence from product surfaces passed
* restored source and export boundaries remained owner-scoped
* audit ledger integrity passed after restore
* audit access remained append-only for the restricted runtime database role
* bounded hosted restore log review passed with metadata-only evidence

These checks verify the product and restore boundaries. They do not replace
owner/legal approval of public wording.

---

# Required Owner Checks

Before public beta, the owner must verify:

* final production Supabase plan retention is compatible with the disclosed
  maximum window
* final production R2 bucket lifecycle/deletion behavior is compatible with the
  disclosed wording
* public Privacy, User Rights, Trust, and Support pages use the same deletion
  and backup language
* deletion wording does not promise instant removal from all backups
* backup wording does not imply backups are available for support browsing,
  analytics, AI training, or product exploration

---

# Required Legal Checks

Before public beta, attorney review must confirm:

* backup/deletion wording is legally acceptable
* Privacy Policy retention language matches the final production posture
* User Rights language does not overpromise deletion behavior
* support language does not invite users to disclose full manuscripts by
  default
* provider and backup disclosures remain consistent

---

# Review Checklist

| Check | Status | Evidence |
| --- | --- | --- |
| Production database backup provider selected | selected | Supabase managed PostgreSQL |
| Production object storage provider selected | selected | Cloudflare R2 private bucket |
| Active deletion removes active product data | verified | deletion and restore drill evidence |
| Isolated restore drill passed | verified | `docs/AEVRYN_RESTORE_AUDIT_DRILL_2026_07_17.md` |
| Source/export boundaries owner-scoped after restore | verified | isolated restore API boundary verification |
| Audit integrity after restore | verified | hosted audit integrity check |
| Hosted restore logs metadata-only | verified | bounded hosted restore log review |
| Supabase source recheck | verified | official source rechecked 2026-08-02 |
| Cloudflare R2 source recheck | verified | official source rechecked 2026-08-02 |
| Production verification tooling | verified | `aevryn backup-retention-config-check` implemented |
| Production Supabase plan retention | blocked | owner verification required |
| Production R2 lifecycle/deletion policy | blocked | owner verification required |
| Final public wording consistency | blocked | owner/legal review required |
| Attorney review | blocked | counsel review required |

---

# Acceptance

This worksheet is accepted when:

```text
backup_retention_source_rechecked=true
owner_legal_backup_wording_review=complete
production_supabase_plan_retention=verified
production_r2_lifecycle_policy=verified
public_beta_backup_wording=approved
```

Until then:

```text
Public beta: Blocked
```
