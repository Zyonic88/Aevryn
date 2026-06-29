# Aevryn Production Infrastructure Readiness

> Built by **Aetherra Labs**

This document tracks V2 Release Candidate Readiness Gate 3.

Gate 3 turns local alpha adapters into explicit production infrastructure decisions.

---

# Status

```text
Gate: Production Infrastructure
Status: Not started
Public beta: Blocked
```

Aevryn has local deterministic adapters for private alpha.

Those adapters prove the product contract, but they are not a public-beta production architecture.

---

# Core Rule

```text
Production infrastructure must fail closed and preserve story privacy by default.
```

No production deployment should rely on local JSON storage, local source-byte storage, local-only secrets, implicit browser origins, or an undefined HTTPS edge.

---

# Required Decisions

Public beta remains blocked until these production decisions are selected, documented, implemented, and tested:

* production database
* production object storage
* source upload storage boundary
* export storage boundary
* production identity provider
* production secret manager
* deployment environment separation
* HTTPS and HSTS edge policy
* domain and DNS strategy
* production worker runtime
* production log destination
* production monitoring destination

Proposed decisions are tracked in `docs/AEVRYN_PRODUCTION_INFRASTRUCTURE_DECISIONS.md`.

These decisions must preserve the platform boundaries already documented in `docs/AEVRYN_PROJECT_DATABASE.md`.

The Project Database stores structured records.

Object storage stores uploaded source files, generated exports, and other large file-like content.

---

# Production Database

The production database decision must define:

* database provider
* region or residency posture
* encryption at rest
* connection credential source
* migration process
* backup behavior
* restore testing process
* project/user ownership constraints
* deletion verification behavior

The database must not become raw manuscript storage.

Uploaded file bytes and generated export bytes belong in storage, referenced by metadata records.

---

# Object Storage

The object storage decision must define:

* provider
* bucket or container separation
* encryption at rest
* access-control model
* signed-reference or capability-reference strategy
* upload object naming rules
* export object naming rules
* deletion behavior
* backup or versioning behavior
* lifecycle retention

Storage references must not grant cross-user access.

Storage logs must not expose full source prose or full generated exports.

---

# Identity Provider

The identity provider decision must define:

* provider
* session authority
* password reset behavior
* token expiration behavior
* secure cookie posture if cookies are used
* CSRF posture if cookies are used
* account deletion handoff
* user identifier mapping to Aevryn project ownership

Frontend routing must remain convenience only.

Backend authorization remains the authority for project access.

---

# Secret Manager

The secret manager decision must define where these values live:

* session secrets
* API keys
* worker credentials
* provider credentials
* database credentials
* storage credentials
* deployment webhook secrets

Secrets must not be committed, logged, exported, snapshotted, or included in support bundles.

Secret rotation must be possible without code changes.

---

# Deployment Environment Separation

Production readiness must define separate environments for:

* local development
* test
* staging or release candidate
* production

Each environment must have separate:

* database
* object storage
* secrets
* API keys
* worker credentials
* monitoring destinations

Test or staging data must not silently mix with production user manuscripts.

---

# HTTPS, HSTS, Domain, And DNS

The production edge decision must define:

* public domain
* DNS owner
* TLS certificate source
* HTTPS-only behavior
* HSTS policy
* redirect behavior
* allowed origins
* API base URL
* frontend base URL

Public beta must not expose Aevryn over plain HTTP.

---

# Worker Runtime

The worker runtime decision must define:

* runtime provider
* job queue
* retry behavior
* timeout behavior
* concurrency limits
* provider extraction timeout limits
* poison-job handling
* shutdown and resume behavior
* credential boundary between API and worker

Workers must observe project/story/import boundaries and must not copy full source prose into logs.

---

# Logs And Monitoring

Production logs and monitoring must define:

* destination
* retention
* access controls
* alerting rules
* redaction rules
* request ID propagation
* workflow event retention

Logs and monitoring must remain metadata-only.

They must not contain full manuscripts, full chapters, full AI responses, credentials, tokens, private URLs, hostnames, usernames, or machine-local paths.

---

# Public Beta Blockers

Public beta remains blocked until:

* remaining proposed infrastructure decisions are approved or revised by the project owner
* production database is selected
* production object storage is selected
* production identity provider is selected
* production secret manager is selected
* environment separation is documented
* HTTPS/HSTS edge policy is documented
* domain and DNS strategy is documented
* production worker runtime is documented
* local adapters are disabled or explicitly unavailable for production deployment
* production-like deployment smoke test passes

Decision 1 result:

```text
Managed PostgreSQL is approved as the production Project Database target.
Production startup now rejects local JSON Project Database configuration.
The PostgreSQL Project Database adapter is implemented.
Gate 3 remains blocked by the remaining infrastructure decisions and production-like smoke test.
```

---

# Acceptance

Gate 3 is accepted when:

```text
Aevryn can run in a production-like environment without local-only storage, local-only secrets, undefined browser origins, or undefined HTTPS behavior.
```
