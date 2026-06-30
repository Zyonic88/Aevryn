# Aevryn Production Infrastructure Readiness

> Built by **Aetherra Labs**

This document tracks V2 Release Candidate Readiness Gate 3.

Gate 3 turns local alpha adapters into explicit production infrastructure decisions.

---

# Status

```text
Gate: Production Infrastructure
Status: Started
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
Local PostgreSQL browser smoke passed for the import -> run -> snapshot path.
Gate 3 remains blocked by the remaining infrastructure decisions and production-like smoke test.
```

Next Gate 3 target:

```text
Decision 2 - Object Storage
```

Decision 2 progress:

```text
Cloudflare R2 is approved as the production object storage provider.
General StorageService, LocalFilesystemStorage, and R2Storage adapters are implemented.
Production and non-production PostgreSQL source/import byte wiring can use Cloudflare R2 when AEVRYN_STORAGE_PROVIDER=r2.
New import source-byte references use project-scoped object paths.
Generated export storage service writes bytes through StorageService and records database metadata.
Generated export API and download routes are implemented.
`aevryn storage-smoke` verifies R2 write/read/delete with metadata-only output.
Large snapshot storage remains open only if snapshot payload size justifies object storage.
```

Next Gate 3 target:

```text
Decision 3 - Identity Provider
```

Decision 3 progress:

```text
Production startup now rejects local JSON authentication.
Production startup requires AEVRYN_IDENTITY_PROVIDER=managed and AEVRYN_SESSION_SECRET.
Managed identity provider selection and adapter wiring remain open.
Public beta remains blocked until managed identity is implemented or the owner accepts a documented residual risk.
```

Next Gate 3 target:

```text
Decision 4 - Secret Management
Decision 5 - Environment Separation
```

Decision 4-5 progress:

```text
Production startup now requires AEVRYN_SECRET_MANAGER=deployment.
Production startup now requires AEVRYN_ENVIRONMENT_NAME=production.
This prevents production from silently using local-only secrets or an ambiguous environment label.
Specific hosted secret manager and staging/production deployment targets remain open.
```

Next Gate 3 target:

```text
Decision 6 - HTTPS, HSTS, Domain, And DNS
```

Decision 6 progress:

```text
Production CORS origins must be explicit HTTPS origins.
Production startup now requires AEVRYN_PUBLIC_FRONTEND_BASE_URL.
Production startup now requires AEVRYN_PUBLIC_API_BASE_URL.
Production startup now requires AEVRYN_HTTPS_ONLY=true.
Production startup now requires AEVRYN_HSTS_ENABLED=true.
Domain, DNS provider, TLS certificate source, and hosted edge implementation remain open.
```

Next Gate 3 target:

```text
Decision 7 - API And Worker Runtime
```

Decision 7 progress:

```text
Production startup now requires AEVRYN_WORKER_RUNTIME=managed.
Production startup now requires AEVRYN_WORKER_QUEUE_PROVIDER=managed.
Production startup now requires AEVRYN_WORKER_API_KEY.
Production startup now requires AEVRYN_WORKER_TIMEOUT_SECONDS.
Production startup now requires AEVRYN_WORKER_MAX_RETRIES.
Production startup now requires AEVRYN_WORKER_CONCURRENCY.
Managed worker runtime, managed queue provider, retry behavior, and shutdown/resume implementation remain open.
```

---

# Acceptance

Gate 3 is accepted when:

```text
Aevryn can run in a production-like environment without local-only storage, local-only secrets, undefined browser origins, or undefined HTTPS behavior.
```
