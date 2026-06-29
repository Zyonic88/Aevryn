# Aevryn Security

> Built by **Aetherra Labs**

Security is architecture, not a feature.

Aevryn will eventually protect user accounts, email addresses, password hashes, sessions, manuscripts, generated canon, exports, usage history, API credentials, and future payment-adjacent metadata. Those assets must be treated as valuable before the first public user uploads a story.

Phase 11 creates the security architecture required before public beta.

---

# Core Rule

```text
Trust is designed.
Not bolted on.
```

Aevryn must fail closed in production, preserve least privilege across every boundary, and keep story content private by default.

---

# Security Layers

## Layer 1 - Identity

Identity answers:

```text
Who are you?
```

Existing foundations:

* password hashing
* session tokens
* session expiration
* password reset
* authenticated project routes

Phase 11 hardening should verify:

* password policy remains explicit
* token storage and session lifecycle are bounded
* reset tokens expire and cannot be reused
* auth failures use stable machine-readable errors
* secrets and tokens are never logged
* production identity configuration fails closed when required settings are missing

## Layer 2 - Authorization

Authorization answers:

```text
What are you allowed to access?
```

Every persisted user object must remain inside an ownership boundary.

Required guarantees:

* User A cannot read User B's projects.
* User A cannot list User B's stories.
* User A cannot read, submit, retry, delete, export, or snapshot User B's imports or runs.
* Worker routes cannot move data across project or story scope.
* Frontend routes never grant authority; backend authorization is the source of truth.
* Cross-user access attempts are tested explicitly.

## Layer 3 - Story Privacy

Uploaded stories are sacred user data.

Required principles:

* Uploaded stories belong to the creator.
* Generated canon belongs to the creator.
* Generated exports belong to the creator.
* Aetherra Labs does not claim ownership of uploaded stories.
* Aetherra Labs does not train models on user projects without explicit opt-in.
* Aetherra Labs does not expose source prose in monitoring, logs, diagnostics, metrics, or support surfaces.
* Deleted stories are actually deleted from Aevryn-owned metadata and source storage.

## Layer 4 - Data Protection

Data protection answers:

```text
How is stored data protected if a boundary fails?
```

Phase 11 should decide and document:

* encryption requirements for manuscripts and generated exports
* encryption requirements for database backups
* storage-reference signing or capability-style references
* secret storage for API keys and worker credentials
* key rotation expectations
* safe migration behavior for plaintext local development state
* deletion verification for source bytes and metadata

Local JSON and filesystem adapters are development adapters. Production storage must define stronger confidentiality, integrity, recovery, and deletion guarantees.

## Layer 5 - API Security

The Phase 11 API hardening contract is documented in `docs/AEVRYN_API_SECURITY_HARDENING.md`.

API hardening includes:

* request validation
* upload validation
* request size limits
* rate limiting
* CORS policy
* CSRF posture where browser cookies are introduced
* timeout policy
* stable security error codes
* secure response headers
* dependency auditing
* static security scanning
* repository secret scanning

Mutation routes must remain authenticated and authorization-scoped.

Web Import must remain unavailable until permission, copyright, anti-abuse, and network security rules are designed.

## Layer 6 - Infrastructure

Infrastructure hardening includes:

* HTTPS-only production traffic
* secure cookie policy if cookies replace bearer storage
* production secret management
* database credential boundaries
* object-storage credential boundaries
* worker credential boundaries
* deployment environment separation
* backup encryption
* restore testing
* incident rollback and recovery procedures

Production should fail closed when required security configuration is missing.

## Layer 7 - Audit Ledger

Aevryn should adopt an append-only audit ledger for security-relevant and workflow-relevant events.

The ledger should be:

* append-only
* hash chained
* tamper evident
* metadata-only
* scoped by user/project/story where appropriate
* free of full source prose
* free of full AI responses
* useful for support, debugging, operational readiness, and enterprise trust

Candidate events:

* user registered
* login succeeded
* login failed
* project created
* story created
* story deleted
* import saved
* run submitted
* worker started
* worker failed
* worker succeeded
* snapshot created
* export generated
* settings changed
* security configuration failure

Audit records must not become a hidden copy of deleted manuscripts.

---

# AI Privacy Boundary

Aevryn's AI boundary is unusually sensitive because the input is unpublished creative work.

Phase 11 must define:

* which model providers, if any, can receive user story content
* whether user content is retained by providers
* how opt-in training/donation would work later
* how source prose is redacted from logs and diagnostics
* how support workflows avoid accessing manuscripts by default
* how users are told what is sent, stored, retained, and deleted

Default posture:

```text
No training on user stories.
No hidden data donation.
No support access by default.
No ownership claim over user work.
```

---

# Verification

Phase 11 should add repeatable security gates.

Minimum gate categories:

* authentication regression tests
* authorization boundary tests
* deletion tests
* no-source-prose logging tests
* upload validation tests
* CORS/security-header tests
* request-size and timeout tests
* dependency audit
* repository secret scan
* static security scan
* audit-ledger integrity tests

The security gate must be repeatable before public beta.

---

# Out Of Scope

Phase 11 does not include:

* new product features
* public launch marketing
* payments implementation
* collaboration features
* image generation
* video generation
* chatbot behavior
* admin-console expansion beyond security verification needs

Phase 11 is about trust.
