# Aevryn Backup Retention Production Verification

> Built by **Aetherra Labs**

This document records the production verification path for Aevryn backup
retention, Supabase managed PostgreSQL backup retention, and Cloudflare R2
object deletion/lifecycle posture.

It is not legal advice.

It does not approve public beta.

---

# Status

```text
Verification: Production backup retention configuration
Status: Owner production values verified
Public beta: Blocked
```

---

# Core Rule

```text
Deletion removes active product data. Backups expire on a disclosed schedule.
```

Public backup wording must match the production database plan, production
object-storage deletion behavior, and any lifecycle policy used for backup or
temporary object expiration.

---

# Metadata-Only Verification Command

Run this from a production-like operator shell after setting the non-secret
declaration values and R2 metadata credentials:

```powershell
$env:AEVRYN_BACKUP_RETENTION_MAX_DAYS="30"
$env:AEVRYN_SUPABASE_PLAN="<pro|team|enterprise>"
$env:AEVRYN_SUPABASE_BACKUP_RETENTION_DAYS="<7|14|30>"
$env:AEVRYN_R2_DELETION_POLICY="<direct_delete|lifecycle_expiration>"

python -m aevryn.cli backup-retention-config-check
```

If `AEVRYN_R2_DELETION_POLICY=lifecycle_expiration`, the shell must also have
the R2 bucket metadata variables configured so the checker can read lifecycle
rules:

```powershell
$env:AEVRYN_R2_BUCKET="<private-production-bucket>"
$env:AEVRYN_R2_ENDPOINT_URL="https://<account_id>.r2.cloudflarestorage.com"
$env:AEVRYN_R2_ACCESS_KEY_ID="<secret>"
$env:AEVRYN_R2_SECRET_ACCESS_KEY="<secret>"
```

Do not paste secrets into this document.

Expected metadata-only output:

```text
backup_retention_max_days=30
supabase_plan=<plan>
supabase_backup_retention_days=<days>
supabase_retention_within_public_window=True
r2_deletion_policy=<direct_delete|lifecycle_expiration>
r2_lifecycle_rules_checked=<count>
r2_lifecycle_expiration_days=<days|not_applicable>
secrets_printed=0
ok=backup_retention_config_contract_checked
```

---

# Production Declaration Rules

The checker fails closed if:

* `AEVRYN_BACKUP_RETENTION_MAX_DAYS` is greater than `30`
* declared Supabase retention exceeds the public maximum
* declared Supabase retention exceeds the documented daily-backup window for
  the selected plan
* R2 deletion policy is neither `direct_delete` nor `lifecycle_expiration`
* lifecycle expiration mode has no enabled lifecycle expiration rule
* lifecycle expiration exceeds the public maximum

The checker prints no database URLs, R2 credentials, object keys, source prose,
storage references, or project identifiers.

---

# Current Production Verification State

The source and implementation posture is ready:

* Supabase source facts were rechecked on 2026-08-02.
* Cloudflare R2 source facts were rechecked on 2026-08-02.
* Active product deletion and restore boundaries passed the restore/audit drill.
* `aevryn backup-retention-config-check` is implemented and covered by tests.

The production owner verified the following metadata-only values on
2026-08-02:

```text
backup_retention_max_days=30
production_supabase_plan=pro
production_supabase_backup_retention_days=7
production_supabase_retention_within_public_window=True
production_r2_deletion_policy=direct_delete
production_r2_lifecycle_rules_checked=0
production_r2_lifecycle_expiration_days=not_applicable
secrets_printed=0
ok=backup_retention_config_contract_checked
```

---

# Public Wording Decision

The current public-beta wording candidate remains:

```text
When you delete a project or story, Aevryn removes it from active
Aevryn-owned product storage. Encrypted production backups may retain deleted
data for up to 30 days for authorized disaster recovery. Backups are not used
for AI training, analytics, support browsing, or product exploration.
```

This wording is compatible with Supabase Pro, Team, and Enterprise daily backup
retention only if the production owner confirms the actual plan/window and the
window is not longer than 30 days.

This wording is compatible with R2 when active deletes remove objects directly
or when any lifecycle-backed temporary retention is no longer than 30 days.

---

# Remaining Blockers

This verification path closes:

* owner production Supabase plan/window verification
* owner production R2 deletion/lifecycle verification

This verification path does not close:

* attorney review of legal-sensitive backup/deletion wording
* final public-beta signoff

---

# Acceptance

```text
backup_retention_verifier=implemented
production_supabase_plan_retention=verified
production_r2_lifecycle_policy=verified
backup_retention_legal_review=blocked
public_beta=blocked_until_final_signoff
```
