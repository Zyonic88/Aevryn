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

The production adapter, core workflow event wiring, configuration-failure event
wiring, release-gate integrity verification command, metadata-only access report
command, and append-only access verification command are implemented.

Hosted production configuration verification, retention enforcement,
access-control verification, hosted release-gate integrity execution, and the
restore/audit drill remain public-beta blockers.

Current implementation:

* `AuditLedger`
* `AuditLedgerRecord`
* `AuditLedgerIntegrityError`
* `PostgresqlAuditLedger`

The implementation lives in `src/aevryn/audit/`.

`PostgresqlAuditLedger` implements the selected PostgreSQL audit storage candidate by creating `audit_ledger_records`, appending records inside a transaction-scoped advisory lock, reloading records in sequence order, and verifying the persisted hash chain.

The release gate can run:

```powershell
python -m aevryn.cli audit-ledger-verify
```

The command reads `AEVRYN_PROJECT_DATABASE_URL`, verifies the PostgreSQL audit
ledger hash chain, prints metadata-only status, and does not print database
credentials.

The access-control review gate can run:

```powershell
python -m aevryn.cli audit-access-verify
```

The command reads `AEVRYN_PROJECT_DATABASE_URL`, verifies that the configured
database role can read and append audit records, verifies that `UPDATE` and
`DELETE` privileges are absent, prints metadata-only status, and does not print
database credentials, roles, usernames, or hostnames.

When an operator needs the underlying privilege facts, the diagnostic report can
run:

```powershell
python -m aevryn.cli audit-access-report
```

The report command reads `AEVRYN_PROJECT_DATABASE_URL`, reports audit table
presence and current database privileges as metadata, does not read audit rows,
and does not print database credentials, roles, usernames, or hostnames.

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

# Implemented Event Types

The API now appends metadata-only records for:

* `user_registered`
* `login_succeeded`
* `login_failed`
* `password_reset_requested`
* `password_reset_completed`
* `project_created`
* `project_deleted`
* `settings_changed`
* `cross_user_access_attempt`
* `story_created`
* `story_deleted`
* `import_saved`
* `run_submitted`
* `worker_processed`
* `snapshot_created`
* `export_generated`
* `security_configuration_failed`

The `security_configuration_failed` event is emitted by the production
configuration check when a PostgreSQL audit ledger can be constructed from the
provided deployment settings. If the audit storage settings themselves are
missing or unreachable, Aevryn still fails closed and does not claim an audit
record was written.

Event types are stable machine-readable tokens.

---

# Public Beta Blockers

Audit ledger work does not unblock public beta until:

* hosted production configuration verifies the PostgreSQL audit adapter
* audit retention policy is enforced or operationally verified
* hosted audit access verification and report are recorded and reviewed
* deletion events are verified to remain metadata-only
* hosted ledger integrity verification is recorded in the release gate
* restore/audit drill results are recorded with `docs/AEVRYN_RESTORE_AUDIT_DRILL_RECORD.md`
