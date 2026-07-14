# Aevryn Audit Ledger

> Built by **Aetherra Labs**

The audit ledger is Aevryn's tamper-evident record of security-relevant and workflow-relevant events.

Core rule:

```text
Audit records explain what happened.
They never preserve the private thing that happened.
```

---

# Phase 11 Scope

Phase 11 introduces the audit ledger contract and a deterministic in-memory implementation.

The public-beta production ledger storage candidate is selected in `docs/AEVRYN_AUDIT_STORAGE_POLICY_DECISION.md`.

The selected candidate is managed PostgreSQL audit tables owned by Aevryn's Project Database environment.

The production adapter, event wiring, retention enforcement, access-control verification, and restore/audit drill remain public-beta blockers.

Current implementation:

* `AuditLedger`
* `AuditLedgerRecord`
* `AuditLedgerIntegrityError`
* `PostgresqlAuditLedger`

The implementation lives in `src/aevryn/audit/`.

`PostgresqlAuditLedger` implements the selected PostgreSQL audit storage candidate by creating `audit_ledger_records`, appending records inside a locked transaction, reloading records in sequence order, and verifying the persisted hash chain.

---

# Required Properties

Audit records are:

* append-only
* sequence ordered
* hash chained
* tamper evident
* metadata-only
* scoped by actor, project, and story where appropriate
* free of source prose
* free of full AI responses
* free of credentials, tokens, password hashes, API keys, local paths, hostnames, and usernames

Each record includes:

* sequence
* event type
* occurrence time
* actor ID
* project ID
* story ID
* concise summary
* concise metadata
* previous hash
* record hash

---

# Hash Chain

Each record hash is calculated from a deterministic JSON payload containing record metadata and the previous record hash.

The first record uses a zero-value genesis hash.

Verification fails if:

* a sequence number changes
* a record is reordered
* a previous hash changes
* a record field changes without recomputing the chain

This makes accidental or malicious tampering detectable.

---

# Metadata-Only Boundary

Audit metadata rejects likely private payload fields, including:

* source text
* source prose
* full manuscripts
* full AI responses
* serialized output
* credentials
* tokens
* API keys
* secrets
* local machine paths

Summaries and metadata values must be concise single-line text.

Deletion events must describe deletion without copying deleted content.

Example:

```text
story_deleted | Story deleted. | import_count=2 snapshot_count=1
```

Not allowed:

```text
story_deleted | Deleted story text: ...
```

---

# Candidate Event Types

Initial event types should include:

* `user_registered`
* `login_succeeded`
* `login_failed`
* `project_created`
* `story_created`
* `story_deleted`
* `import_saved`
* `run_submitted`
* `worker_started`
* `worker_failed`
* `worker_succeeded`
* `snapshot_created`
* `export_generated`
* `settings_changed`
* `security_configuration_failed`

Event types are stable machine-readable tokens.

---

# Public Beta Blockers

Audit ledger work does not unblock public beta until:

* production storage adapter for audit records is configured in production
* audit retention policy is enforced or operationally verified
* audit access controls are configured and reviewed
* security-relevant API and worker events are wired into the ledger
* deletion events are verified to remain metadata-only
* ledger integrity verification is part of the release gate
* restore/audit drill results are recorded with `docs/AEVRYN_RESTORE_AUDIT_DRILL_RECORD.md`
