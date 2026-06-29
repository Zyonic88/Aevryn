# Aevryn Data Retention Policy

> Built by **Aetherra Labs**

This engineering policy defines the intended retention posture for Aevryn.

This is not a final legal privacy policy.

---

# Core Rule

```text
Keep data only while it has a clear product, security, legal, or recovery purpose.
```

---

# Accounts

Account records are retained while the account is active.

Future account deletion must remove or anonymize active account data unless legal, fraud-prevention, billing, or security obligations require limited retention.

---

# Projects

Project metadata is retained while the project exists.

Deleting a project or story must remove active project/story data scoped to that deletion.

---

# Uploads

Uploaded source files and pasted source text are retained only as active project data needed for import, processing, rebuild, and user workflow.

Deleted story uploads must be removed from active Aevryn-owned storage.

---

# Snapshots

Canon snapshots and generated output records are retained while the project/story exists.

Deleted story snapshots must be removed from active Aevryn-owned storage.

---

# Logs

Logs must be metadata-only.

Logs must not contain full source prose, full AI payloads, credentials, tokens, local paths, hostnames, usernames, or serialized exports.

Production log retention windows must be selected before public beta.

---

# Exports

Exports are retained while the project/story exists unless the user deletes them or deletes the containing project/story.

---

# Audit Records

Audit records are retained for security, integrity, support, and operational accountability.

Audit records must remain metadata-only and must not become hidden copies of deleted manuscripts.

Production audit retention windows must be selected before public beta.

---

# Backups

Backup retention is defined in `docs/AEVRYN_BACKUP_RETENTION.md`.

Production backup windows must be disclosed before public beta.
