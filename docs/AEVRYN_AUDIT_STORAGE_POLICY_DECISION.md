# Aevryn Audit Storage Policy Decision

> Built by **Aetherra Labs**

Decision: Audit storage policy candidate

Status: Selected for owner/security review

Public beta: Blocked

---

# Core Rule

```text
Audit records explain what happened.
They never preserve the private thing that happened.
```

Audit storage exists to support security, recovery, incident response, and workflow accountability.

Audit storage must never become hidden story storage.

---

# Selected Candidate

For the public-beta candidate, production audit records should be stored in managed PostgreSQL audit tables owned by Aevryn's Project Database environment.

This keeps the first production audit ledger close to the metadata it explains while preserving a clean future path to dedicated ledger storage if scale, compliance, or enterprise requirements demand it.

The candidate storage model is:

```text
Aevryn API / Worker
-> AuditLedger
-> PostgreSQL audit schema or audit tables
-> hash-chain verification
```

The application write path must be append-only.

Administrative database access must be limited, audited, and treated as a privileged production operation.

---

# Required Record Shape

Production audit records should store only metadata needed to explain an event:

* audit record ID
* sequence or monotonic ordering value
* event type
* occurred_at
* actor ID or service actor ID
* user ID when available
* project ID when available
* story ID when available
* import ID when available
* run ID when available
* snapshot ID when available
* export ID when available
* concise event summary
* concise metadata
* previous hash
* record hash

Event types must remain stable machine-readable tokens.

---

# Forbidden Data

Audit records must not store:

* full manuscripts
* full source prose
* full imported chapter text
* full AI provider prompts
* full AI provider responses
* generated exports
* credentials
* tokens
* password hashes
* API keys
* database URLs
* private URLs
* hostnames
* usernames
* machine-local paths
* serialized project snapshots

If an audit record needs to reference private content, it must reference metadata identifiers only.

---

# Retention Candidate

Public-beta audit records should be retained for up to 1 year unless owner/legal/security review selects a different production window.

Audit records may remain after project deletion when needed for security, abuse prevention, legal accountability, incident response, or integrity verification.

Any audit record that remains after deletion must be metadata-only and must not contain the deleted story, source prose, AI payloads, exports, or private storage bytes.

Deletion events may outlive deleted content as evidence that deletion occurred.

---

# Access Controls

Audit access must be restricted to authorized operational, security, or owner review.

Required controls:

* least-privilege database access
* MFA-protected production access
* no casual employee browsing
* read-only inspection by default
* break-glass access documented when used
* audit access events recorded
* access reviewed before public beta

Support workflows should use product metadata and user-visible status first.

Direct audit inspection should be reserved for security, recovery, incident response, or authorized troubleshooting.

---

# Integrity Verification

The release gate must include audit integrity verification before public beta.

Required verification:

* append-only application write path exists
* hash-chain verification passes
* tamper detection fails closed
* deletion events remain metadata-only
* restore/audit drill confirms ledger integrity after restore
* restore/audit drill confirms logs remain metadata-only

The restore/audit drill record lives in `docs/AEVRYN_RESTORE_AUDIT_DRILL_RECORD.md`.

---

# Implementation Blockers

This document selects the candidate policy.

The PostgreSQL audit storage adapter is implemented as `PostgresqlAuditLedger` in `src/aevryn/audit/postgresql.py`.

The adapter creates the `audit_ledger_records` table, appends records in a locked transaction, reloads records in sequence order, and verifies the persisted hash chain.

Core API and worker workflow events are wired to the configured audit writer.

The covered event set includes registration, login success/failure, password
reset request/completion, project creation/deletion, settings changes, cross-user
settings access denials, story creation/deletion, import save, run submission,
worker drain completion, snapshot creation, and export generation.

Public beta remains blocked until:

* PostgreSQL audit adapter configuration is verified in hosted production
* audit retention behavior is enforced or operationally documented
* audit access controls are configured and reviewed
* hash-chain verification is included in the release gate
* deletion events are verified as metadata-only
* restore/audit drill is completed with dated results

---

# Acceptance

This decision is accepted when:

```text
Production audit records can be stored in managed PostgreSQL as metadata-only,
append-only, tamper-evident records; deletion events can outlive deleted content
without preserving it; and public beta remains blocked until production
configuration verification, retention, access, and restore/audit verification are complete.
```
