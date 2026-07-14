# Aevryn Privacy Policy

> Draft for attorney review before public launch.

This draft describes the intended privacy posture for Aevryn. It is not a substitute for legal review.

---

# Information Collected

Aevryn may collect:

* account information
* authentication/session data
* project metadata
* uploaded files and pasted story text
* generated canon, snapshots, and exports
* usage and diagnostic metadata
* support communications

---

# Cookies

If browser cookies become part of authentication or analytics, Aevryn must disclose cookie purpose, duration, and controls.

Current V2 alpha session behavior is bearer-session based.

---

# Analytics

Analytics must be privacy-preserving.

Analytics must not contain full source prose, full AI payloads, credentials, tokens, local paths, hostnames, usernames, or serialized exports.

---

# Authentication

Aevryn uses authentication data to create accounts, log users in, maintain sessions, and protect project access.

Password hashes and session tokens must be protected and must not be logged.

---

# Uploaded Files

Uploaded stories belong to their creators.

Aevryn uses uploaded files to inspect, import, process, display, and export project data for the user.

Aetherra Labs does not train on uploaded stories without explicit opt-in.

---

# Data Retention

Retention principles are defined in `docs/DATA_RETENTION_POLICY.md`.

Deletion removes active Aevryn-owned project/story storage. The current public-beta wording candidate says encrypted production backups may retain deleted project or story data for up to 30 days for authorized disaster recovery only.

Backup retention wording is tracked in `docs/AEVRYN_BACKUP_RETENTION_DECISION.md` and requires legal review before public launch.

---

# Third-Party Processors

Before public beta, Aevryn must disclose third-party processors that may receive user data, including authentication, hosting, storage, analytics, payment, support, and AI providers.

---

# User Rights

User rights are described in `docs/AEVRYN_USER_RIGHTS.md`.

Future public policy must describe rights to access, export, correct, delete, object, or restrict processing where applicable law requires.

---

# Contact Information

Target privacy contact:

```text
privacy@aevryn.ai
```

This alias is provisioned and tested for inbound receipt, outbound product-domain sending, SPF, DKIM, DMARC, and MFA-protected operator access.

Public privacy contact information must be published accurately before public launch.

Public privacy contact readiness is tracked in `docs/AEVRYN_PUBLIC_SUPPORT_READINESS.md`.
