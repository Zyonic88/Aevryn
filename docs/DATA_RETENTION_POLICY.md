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

Deleting a project or story must remove active project/story data scoped to that deletion, including queued or completed background job metadata.

---

# Uploads

Uploaded source files and pasted source text are retained only as active project data needed for import, processing, rebuild, and user workflow.

Deleted story uploads must be removed from active Aevryn-owned storage.

---

# Snapshots

Canon snapshots and generated output records are retained while the project/story exists.

Deleted story snapshots must be removed from active Aevryn-owned storage.

---

# Background Jobs

Background job metadata is retained only while the containing project/story exists and while it is needed for workflow observability, retry, and support.

Project or story deletion must remove matching background job rows from active Aevryn-owned storage.

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

The public-beta audit storage and retention candidate is recorded in `docs/AEVRYN_AUDIT_STORAGE_POLICY_DECISION.md`.

Candidate retention is up to 1 year unless owner/legal/security review selects a different production window.

Audit records may remain after project deletion when needed for security, abuse prevention, legal accountability, incident response, or integrity verification.

Any audit record that remains after deletion must be metadata-only and must not contain deleted story content, source prose, AI payloads, exports, or private storage bytes.

Production audit retention enforcement must be implemented or operationally verified before public beta.

---

# Backups

Backup retention is defined in `docs/AEVRYN_BACKUP_RETENTION.md`.

The selected public-beta wording candidate is recorded in `docs/AEVRYN_BACKUP_RETENTION_DECISION.md`.

Production backup behavior must support the disclosed window before public beta.
