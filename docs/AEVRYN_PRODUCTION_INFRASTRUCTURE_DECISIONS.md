# Aevryn Production Infrastructure Decisions

> Built by **Aetherra Labs**

This document records proposed production infrastructure decisions for V2 Release Candidate Readiness Gate 3.

These decisions are implementation-tracked below.

They are the recommended public-beta architecture shape to approve, revise, or replace before implementation.

---

# Status

```text
Gate: Production Infrastructure
Decision status: Decisions 1-2 approved
Owner approval: Decisions 1-2 approved
Implementation status: Decision 1 implemented; Decision 2 source/import/export storage wiring started
Public beta: Blocked
```

Gate 3 remains blocked until the approved decisions are implemented and verified in a production-like smoke test.

---

# Core Rule

```text
Production infrastructure must fail closed and preserve story privacy by default.
```

The public-beta platform must not depend on local JSON storage, local source-byte storage, local-only secrets, implicit browser origins, or plain HTTP.

---

# Recommended Public-Beta Architecture

For public beta, Aevryn should use a conservative managed-services architecture:

* managed PostgreSQL for structured platform records
* private object storage for uploaded source files and generated exports
* managed identity provider for user accounts, sessions, and password recovery
* managed secret storage for provider credentials, database credentials, session secrets, and worker credentials
* separate API and worker runtimes
* explicit environment separation for local, test, staging, and production
* HTTPS-only public edge with HSTS
* hosted logs and monitoring with metadata-only redaction rules

This architecture keeps the V2 product boundaries intact while replacing local alpha adapters with production-grade services.

---

# Decision 1 - Production Database

Approved decision:

```text
Use managed PostgreSQL for production Project Database storage.
```

Rationale:

* Aevryn needs relational ownership boundaries between users, projects, stories, imports, runs, snapshots, exports, and settings.
* PostgreSQL supports transactions, constraints, migrations, indexes, and backup tooling.
* The existing Project Database boundary already treats structured records separately from uploaded source bytes.

Requirements:

* encrypted at rest
* connection credentials stored outside source control
* migrations required before production deploy
* backups enabled
* restore test required before public beta
* row ownership constraints enforced by application authorization
* no raw manuscript file bytes stored directly in database records

Open decision:

```text
Provider not selected.
```

Examples of acceptable provider classes include managed PostgreSQL from the chosen deployment platform or a dedicated managed database provider.

Implementation contract:

```text
AEVRYN_DEPLOYMENT_ENV=production requires AEVRYN_PROJECT_DATABASE_ADAPTER=postgresql and AEVRYN_PROJECT_DATABASE_URL.
Production mode rejects AEVRYN_PROJECT_DATABASE_PATH because local JSON storage is not allowed for production.
```

Current implementation result:

```text
PostgreSQL Project Database adapter is implemented behind the optional postgresql dependency.
Production startup rejects local JSON Project Database configuration.
Local PostgreSQL browser/API smoke passed for import processing and canon snapshot creation.
Public beta remains blocked by the remaining production infrastructure decisions and smoke tests.
```

---

# Decision 2 - Object Storage

Approved decision:

```text
Use private Cloudflare R2 object storage for uploaded source files, generated exports, large snapshots when needed, and future media assets.
```

Rationale:

* Uploaded manuscripts and generated exports are file-like content.
* Large binary or text blobs should not live directly in the Project Database.
* Cloudflare R2 gives Aevryn a private S3-compatible storage-reference model.

Requirements:

* private buckets
* encryption at rest
* separate source-upload and export prefixes or containers
* storage references scoped by user, project, story, and object kind
* no public object listing
* no cross-user storage references
* deletion operation for active-storage objects
* lifecycle and backup behavior documented before public beta

Approved provider:

```text
Cloudflare R2.
```

Recommended bucket split:

```text
aevryn-dev
aevryn-alpha
aevryn-prod
```

Recommended object paths:

```text
projects/{project_id}/imports/{import_id}/source.epub
projects/{project_id}/exports/{export_id}/character_sheet.md
projects/{project_id}/snapshots/{snapshot_id}.json
```

Storage rule:

```text
Storage owns bytes. Database owns references. Engine owns meaning.
```

Database reference metadata:

* project_id
* story_id
* import_id
* export_id
* storage_ref
* filename
* content_type
* size
* checksum
* created_at

Private access rules:

* never make manuscript buckets public
* frontend must not know R2 credentials
* API and worker write files
* database stores only references and metadata
* signed URLs are future-only and deliberate

Current implementation result:

```text
General StorageService boundary is implemented.
LocalFilesystemStorage development adapter is implemented.
Cloudflare R2 storage adapter is implemented behind the optional object-storage dependency.
Production source/import byte wiring can use Cloudflare R2.
Generated export storage service writes bytes through StorageService and records database metadata.
Generated export API/download routes are not implemented yet.
Large snapshot object storage is not implemented yet.
Import storage references still use the existing story/import reference shape until the project-scoped reference migration is implemented.
```

---

# Decision 3 - Identity Provider

Recommended decision:

```text
Use a managed identity provider for public-beta authentication.
```

Rationale:

* Public users need reliable registration, login, session expiration, and password recovery.
* Aevryn should not invent production identity infrastructure when managed identity providers already solve common account-security workflows.
* Backend authorization must still enforce project ownership regardless of frontend route state.

Requirements:

* email/password or equivalent account login
* password reset
* session expiration
* stable external user identifier
* backend mapping from external identity to Aevryn user records
* account deletion handoff
* secure cookie and CSRF posture if browser cookies become session authority

Open decision:

```text
Provider not selected.
Session authority not finalized.
```

---

# Decision 4 - Secret Management

Recommended decision:

```text
Use managed deployment secrets for public beta and graduate to a dedicated secret manager when infrastructure complexity requires it.
```

Rationale:

* Public beta needs secrets outside source control immediately.
* Deployment-hosted secrets can be acceptable for an early single-environment public beta when access is narrow and auditable.
* A dedicated secret manager may become necessary when multiple services, rotations, environments, or operators expand.

Secrets covered:

* session secrets
* API keys
* worker credentials
* OpenAI or other provider credentials
* database credentials
* storage credentials
* deployment webhook secrets

Requirements:

* secrets are never committed
* secrets are never logged
* rotation requires no code changes
* staging and production secrets are separate
* provider keys are scoped to the minimum required access

Open decision:

```text
Secret manager provider not selected.
```

---

# Decision 5 - Environment Separation

Recommended decision:

```text
Maintain separate local, test, staging, and production environments.
```

Requirements:

* separate database per environment
* separate object storage per environment
* separate secrets per environment
* separate worker credentials per environment
* separate monitoring destinations per environment
* production data must not be copied into local development
* staging must not silently point at production storage

Public beta must include at least:

* local development
* staging or release-candidate environment
* production

---

# Decision 6 - HTTPS, HSTS, Domain, And DNS

Recommended decision:

```text
Serve public beta over HTTPS only with HSTS enabled after domain behavior is verified.
```

Requirements:

* public domain selected
* DNS owner selected
* TLS certificate source selected
* HTTP redirects to HTTPS
* HSTS policy documented
* frontend origin explicit
* API origin explicit
* CORS origins explicit
* no wildcard public CORS

Open decision:

```text
Domain and DNS provider not selected.
```

---

# Decision 7 - API And Worker Runtime

Recommended decision:

```text
Run API and worker as separate runtime processes with separate credentials.
```

Rationale:

* The API handles user requests.
* Workers handle processing and provider-backed extraction.
* Separate credentials reduce blast radius and make queue/retry behavior easier to reason about.

Requirements:

* worker queue selected
* worker timeout limits selected
* retry policy selected
* poison-job handling selected
* shutdown/resume behavior documented
* worker credentials separate from browser-facing API sessions
* worker logs remain metadata-only

Open decision:

```text
Worker runtime and queue provider not selected.
```

---

# Decision 8 - Logs And Monitoring

Recommended decision:

```text
Use hosted logs and monitoring with metadata-only redaction rules.
```

Requirements:

* request ID propagation
* workflow event visibility
* failure summaries
* security configuration failure alerts
* worker failure alerts
* provider failure alerts
* no full manuscripts
* no full chapters
* no full AI responses
* no credentials, tokens, private URLs, hostnames, usernames, or machine-local paths

Open decision:

```text
Log and monitoring provider not selected.
Retention window not selected.
```

---

# Production Adapter Rule

Production deployment must fail closed if local-only adapters are selected accidentally.

Before public beta, startup validation should reject production configuration that uses:

* local JSON Project Database storage
* local auth storage
* local source-byte storage
* missing `AEVRYN_STORAGE_PROVIDER=r2`
* missing private R2 bucket
* missing R2 account ID, endpoint URL, access key ID, or secret access key
* missing explicit CORS origins
* missing API or worker credentials
* missing session secret
* missing provider credentials when provider-backed extraction is enabled

---

# Implementation Order

Recommended implementation order:

1. Select providers and domain.
2. Add production configuration contract.
3. Add PostgreSQL Project Database adapter.
4. Add object-storage source/export adapter.
5. Add managed identity integration.
6. Add worker queue/runtime integration.
7. Add hosted logs and monitoring redaction rules.
8. Add production-like smoke environment.
9. Run Gate 8 release-candidate test pass.

---

# Current Public Beta Result

```text
Public beta remains blocked.
Reason: Production infrastructure decisions are proposed but not approved, implemented, or smoke-tested.
```
