# Aevryn Backend API

> Built by **Aetherra Labs**

This document defines the Version 2 Phase 1 Backend API boundary.

The API is a contract layer.

It is not the engine.

It is not the frontend.

It is not the database.

---

# What Is It?

The Backend API is the stable HTTP contract that platform clients use to access Aevryn.

In Phase 1, it begins as a thin FastAPI application that calls the existing Aevryn Engine through Project Manager and Story Import.

---

# Why Does It Exist?

Version 1 proved the engine through the CLI.

Version 2 needs the same workflows exposed through an API so the website can become a client instead of a place where business logic hides.

The API exists so every future client uses the same contract:

```text
Client
-> API
-> Project Manager
-> Aevryn Engine
```

---

# What Authority Does It Own?

The Backend API owns:

* Route definitions
* Request validation
* Response models
* API error shape
* API versioning
* Optional workflow authentication enforcement
* Client-facing source-format metadata
* Temporary request file handling for import inspection

---

# What Does It NOT Own?

The Backend API does not own:

* Canon truth
* Timeline truth
* Evidence validation
* Story Import parsing
* Entity extraction rules
* Presentation view construction
* Export serialization
* User interface behavior
* Persistent project storage
* Full user accounts or password authentication
* Background job execution

---

# Phase 1 Initial Routes

## Application Configuration

The Backend API can be created with explicit CORS origins for browser clients.

By default, CORS is disabled.

Example:

```python
from aevryn.api import create_app

app = create_app(allowed_origins=("http://localhost:5173",))
```

Deployment environments may also set:

```text
AEVRYN_API_ALLOWED_ORIGINS=http://localhost:5173,https://app.example.com
```

The module-level ASGI app reads that environment variable:

```text
uvicorn aevryn.api.app:app
```

## Production Fail-Closed Mode

Production mode is explicit:

```text
AEVRYN_DEPLOYMENT_ENV=production
```

When production mode is enabled, `create_app_from_env` refuses to start unless these security-critical settings are present:

* `AEVRYN_PROJECT_DATABASE_ADAPTER=postgresql`
* `AEVRYN_PROJECT_DATABASE_URL`
* `AEVRYN_API_ALLOWED_ORIGINS`
* `AEVRYN_API_KEYS`
* `AEVRYN_STORAGE_PROVIDER=r2`
* `AEVRYN_R2_BUCKET`
* `AEVRYN_R2_ACCOUNT_ID`
* `AEVRYN_R2_ENDPOINT_URL`
* `AEVRYN_R2_ACCESS_KEY_ID`
* `AEVRYN_R2_SECRET_ACCESS_KEY`

Production CORS origins must be HTTPS only. Production also requires public edge declarations:

```text
AEVRYN_PUBLIC_FRONTEND_BASE_URL=https://app.aevryn.ai
AEVRYN_PUBLIC_API_BASE_URL=https://api.aevryn.ai
AEVRYN_HTTPS_ONLY=true
AEVRYN_HSTS_ENABLED=true
```

This prevents public deployments from accidentally starting with stateless storage, local source-byte storage, broad or absent browser-origin policy, missing HTTPS/HSTS edge posture, or unprotected workflow routes.

Production mode rejects `AEVRYN_PROJECT_DATABASE_PATH` because that path selects the local JSON adapter.
Production mode rejects `AEVRYN_IMPORT_STORAGE_PATH` because that path selects local filesystem source-byte storage.

The PostgreSQL Project Database adapter is available through the optional `postgresql` dependencies. Cloudflare R2 source/import storage is available through the optional `object-storage` dependencies. Generated export writes can use the same `StorageService` boundary and record export metadata in the Project Database. Public-beta production startup still remains blocked by remaining production identity, hosted provider selections, and production-like smoke-test signoff.

For local development, the Aevryn CLI can launch the same API:

```text
aevryn api --host 127.0.0.1 --port 8000 --allowed-origin http://localhost:5173
```

When `--reload` is enabled, the CLI uses the environment-backed app factory so
Uvicorn can reload from an import string safely.

The value must be a comma-separated list of explicit origins.

Wildcard origins are rejected.

The API should never use broad browser access by accident.

Allowed origins are a platform deployment decision, not an engine decision.

## Local Project Storage

Phase 6 project routes require an explicit Project Database adapter.

For local durable project metadata, set:

```text
AEVRYN_PROJECT_DATABASE_PATH=C:\Users\enigm\Documents\Aevryn\.local\project_database.json
```

Optional explicit local adapter selector:

```text
AEVRYN_PROJECT_DATABASE_ADAPTER=json
```

For PostgreSQL-backed project metadata, install the optional PostgreSQL dependency and set:

```text
AEVRYN_PROJECT_DATABASE_ADAPTER=postgresql
AEVRYN_PROJECT_DATABASE_URL=postgresql://aevryn_app:<password>@localhost:5432/aevryn_dev
AEVRYN_AUTH_STORE_PATH=C:\Users\enigm\Documents\Aevryn\.local\postgresql_auth.json
AEVRYN_IMPORT_STORAGE_PATH=C:\Users\enigm\Documents\Aevryn\.local\postgresql_imports
```

The database URL must stay local to the machine or deployment secret manager.
Do not commit it, paste it into issue trackers, or print it in logs.

After setting the environment variable, verify the adapter with:

```text
aevryn project-db-smoke
```

The smoke test creates, reads, and deletes one temporary user record. It bootstraps missing schema objects, prints metadata-only results, and never prints the database URL or password.

For local browser testing, the PostgreSQL adapter stores project metadata in PostgreSQL while local development auth/session records and uploaded source bytes remain in the configured filesystem paths above. This keeps the alpha workflow browser-ready without pretending that local JSON auth or local file import storage are final production identity or object-storage systems.

The production source-byte object storage boundary uses Cloudflare R2 through a general `StorageService` interface.
Non-production PostgreSQL environments can also opt into R2 by setting `AEVRYN_STORAGE_PROVIDER=r2`; otherwise they use local filesystem source-byte storage by default.

```text
AEVRYN_STORAGE_PROVIDER=r2
AEVRYN_R2_BUCKET=aevryn-alpha
AEVRYN_R2_ACCOUNT_ID=<account-id>
AEVRYN_R2_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
AEVRYN_R2_ACCESS_KEY_ID=<stored in deployment secrets>
AEVRYN_R2_SECRET_ACCESS_KEY=<stored in deployment secrets>
```

R2 buckets must be private. The frontend must never receive R2 credentials. The API and worker write bytes, and PostgreSQL stores only references and metadata such as `storage_ref`, filename, content type, size, checksum, and timestamps.

After setting the R2 environment variables, verify the adapter with:

```text
aevryn storage-smoke
```

The smoke test writes, reads, and deletes one tiny synthetic private object. It prints metadata-only results and never prints access keys or secret keys.

Metadata-only production configuration contract check:

```text
aevryn production-config-check
```

The check validates that `AEVRYN_DEPLOYMENT_ENV=production` has the fail-closed production startup contract configured. It does not connect to PostgreSQL or R2, and it never prints database URLs, API keys, storage keys, worker keys, or session secrets. Until managed production identity is implemented, a fully configured production contract reports `public_beta=blocked_managed_identity`.

Newly saved import source bytes use project-scoped object references such as:

```text
storage://projects/{project_id}/imports/{import_id}/source.bin
```

Generated export storage service support exists, including generated export API and download routes. Large snapshot object storage remains release-candidate work only if snapshot payload size justifies moving snapshots out of PostgreSQL.

Production identity is intentionally fail-closed until a managed identity provider is selected and wired:

```text
AEVRYN_SECRET_MANAGER=deployment
AEVRYN_ENVIRONMENT_NAME=production
AEVRYN_IDENTITY_PROVIDER=managed
AEVRYN_IDENTITY_PROVIDER_NAME=supabase
AEVRYN_SUPABASE_URL=https://<project-ref>.supabase.co
AEVRYN_SUPABASE_JWKS_URL=https://<project-ref>.supabase.co/auth/v1/.well-known/jwks.json
AEVRYN_SUPABASE_ANON_KEY=<stored in deployment secrets>
AEVRYN_SUPABASE_SERVICE_ROLE_KEY=<stored in deployment secrets>
AEVRYN_SESSION_AUTHORITY=bearer
AEVRYN_SESSION_SECRET=<stored in deployment secrets>
AEVRYN_PASSWORD_RESET_ENABLED=true
AEVRYN_ACCOUNT_DELETION_HANDOFF_CONFIGURED=true
```

These variables document the production secret, environment, and identity contract, but public beta remains blocked until the Supabase Auth adapter exists. Supabase Auth is the selected managed identity provider. Bearer sessions remain the production contract until cookie-backed sessions and CSRF protection are deliberately implemented. Local JSON authentication and local-only secrets remain private-alpha only.

The managed identity boundary now separates provider token verification from Aevryn ownership records:

```text
Supabase bearer token
-> ManagedIdentityVerifier
-> ManagedIdentity
-> ManagedIdentityAuthenticationAdapter
-> Aevryn UserRecord
```

The boundary maps external provider subjects to stable Aevryn user IDs without storing provider tokens. Supabase RS256 JWT/JWKS verification is implemented behind this boundary. Production startup still remains blocked until the Supabase verifier is wired into the API app factory and covered by production-like smoke execution.

Production worker runtime is intentionally fail-closed until a managed queue/runtime is selected and wired:

```text
AEVRYN_WORKER_RUNTIME=managed
AEVRYN_WORKER_QUEUE_PROVIDER=managed
AEVRYN_WORKER_API_KEY=<stored in deployment secrets>
AEVRYN_WORKER_TIMEOUT_SECONDS=120
AEVRYN_WORKER_MAX_RETRIES=3
AEVRYN_WORKER_CONCURRENCY=1
```

These variables document the production worker contract. The local in-memory queue remains private-alpha only.

Production observability is intentionally fail-closed until hosted logs, hosted monitoring, retention, and security alert routing are selected:

```text
AEVRYN_LOG_DESTINATION=hosted
AEVRYN_MONITORING_DESTINATION=hosted
AEVRYN_LOG_RETENTION_DAYS=30
AEVRYN_MONITORING_RETENTION_DAYS=30
AEVRYN_SECURITY_ALERTS_ENABLED=true
AEVRYN_METADATA_ONLY_LOGGING=true
```

These variables document the production observability contract. Logs and monitoring must remain metadata-only; full manuscripts, full chapters, full AI responses, credentials, tokens, private URLs, hostnames, usernames, and machine-local paths remain out of logs.

Optional explicit authentication store path:

```text
AEVRYN_AUTH_STORE_PATH=C:\Users\enigm\Documents\Aevryn\.local\auth_store.json
```

If `AEVRYN_AUTH_STORE_PATH` is omitted, Aevryn stores local auth records beside the project database using the project database filename plus `_auth.json`.

Optional explicit import content storage path:

```text
AEVRYN_IMPORT_STORAGE_PATH=C:\Users\enigm\Documents\Aevryn\.local\imports
```

If `AEVRYN_IMPORT_STORAGE_PATH` is omitted, Aevryn stores local import source bytes beside the project database using the project database filename plus `_imports`.

When this value is present, `create_app_from_env` wires:

* `JsonProjectRepository` for local Project Database records
* `AuthenticationService` over the same repository for user ownership records
* `JsonAuthenticationStore` for credential hashes, session token hashes, and password reset token hashes
* `FileSystemImportContentStore` for uploaded source bytes referenced by import metadata
* an in-memory background job queue and import snapshot worker handler for local API smoke tests

This means local project records, imported source bytes, credential hashes, session token hashes, and password reset token hashes survive process restarts.

The JSON auth store is a deterministic local adapter, not the final production identity provider.

If `AEVRYN_PROJECT_DATABASE_PATH` is absent, authenticated project routes fail clearly with `project_storage_unavailable` instead of silently creating stateless project shells.

## Worker Extraction Mode

The environment-backed worker defaults to local deterministic extraction.

Default mode:

```text
AEVRYN_EXTRACTION_MODE=demo
```

Provider-backed extraction is opt-in only:

```text
AEVRYN_EXTRACTION_MODE=openai
AEVRYN_OPENAI_API_KEY=...
AEVRYN_OPENAI_MODEL=...
```

Optional provider settings:

```text
AEVRYN_OPENAI_ENDPOINT=https://api.openai.com/v1/responses
AEVRYN_OPENAI_TIMEOUT_SECONDS=30
AEVRYN_OPENAI_MAX_RESPONSE_BYTES=1048576
```

If `AEVRYN_EXTRACTION_MODE` is absent or `demo`, no external model receives story text.

If `AEVRYN_EXTRACTION_MODE=openai`, `AEVRYN_OPENAI_API_KEY` and `AEVRYN_OPENAI_MODEL` are required before the app starts.

Provider-backed extraction runs one evidence-bounded scene request at a time. Very large imports can exceed the default per-request timeout if a provider response stalls. For internal alpha testing, prefer smaller chapter batches first; raise `AEVRYN_OPENAI_TIMEOUT_SECONDS` only when validating large imports and track the latency separately from correctness.

Invalid modes, non-positive timeouts, and non-positive response byte limits fail at app creation time.

## Authentication Middleware

Phase 1 supports optional API-key protection for workflow routes.

This is not full user authentication.

It is a deployment boundary that lets platform clients prove protected API calls before Version 2 adds users, sessions, project permissions, and account recovery.

Configure keys explicitly when creating the app:

```python
from aevryn.api import create_app

app = create_app(api_keys=("local-dev-key",))
```

Deployment environments may also set:

```text
AEVRYN_API_KEYS=local-dev-key,another-key
```

When API keys are configured, Phase 1 workflow routes require either:

* `X-Aevryn-API-Key: <key>`
* `Authorization: Bearer <key>`

Protected routes currently include Version 2 `POST /v2/...` workflow endpoints such as import inspection, extraction application, project output previews, and export previews.

Public discovery routes remain public:

* `GET /v2`
* `GET /v2/health`
* `GET /v2/capabilities`
* `GET /v2/source-formats`
* `GET /openapi.json`

Missing keys return `401 authentication_required`.

Invalid keys return `403 invalid_api_key`.

The middleware does not own user accounts, passwords, sessions, project permissions, or authorization policy. Those belong to later Version 2 authentication and project storage phases.

## OpenAPI Contract

The Backend API exposes FastAPI's OpenAPI schema at:

```text
/openapi.json
```

Routes use stable operation IDs and tags so future frontend tooling can generate
clients without depending on Python function names.

Current route tag groups:

* System
* Import
* Extraction
* Canon
* Timeline
* Projects
* Characters
* Scenes
* Prompts
* World
* Continuity
* Project Outputs
* Exports


## Validation Workflow

The local validation suite remains a CLI-only development workflow in Phase 1.

It is not exposed through the public Backend API.

A future admin-only validation API may be added deliberately, but normal platform clients should not run validation corpus jobs through Phase 1 routes.

## Response Headers

Every Backend API response includes:

```text
X-Aevryn-API-Version: v2
X-Aevryn-Engine: Aevryn
X-Request-ID: <request-id>
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: no-referrer
Permissions-Policy: camera=(), microphone=(), geolocation=()
```

These headers appear on successful responses and structured error responses.

They exist so clients, logs, and future platform tooling can identify the API
contract version without parsing response bodies.

The browser-facing security headers reduce MIME sniffing, clickjacking, referrer leakage, and ambient device-permission exposure. They appear on successful responses and structured error responses.

If a client sends a valid `X-Request-ID` header, the API echoes it.

If the client omits it, or sends a whitespace-bearing value, the API generates
one.

## `GET /v2`

Returns the Version 2 API index.

The response includes:

* API version
* engine name
* platform phase
* entrypoint links
* current platform limits

This route is the simplest discovery entry point for humans, local tools, and
future frontend clients.

## `GET /v2/health`

Returns API health metadata, including metadata-only storage adapter availability.

The route reports whether project storage and import-content storage adapters are configured. It does not read project rows, import bytes, source prose, or engine state.

It does not touch project or engine state.

## `GET /v2/capabilities`

Returns frontend-discoverable Phase 1 API metadata.

The response includes:

* API version
* engine name
* platform phase
* public route list
* supported and deferred source formats
* supported export preview kinds and formats
* current platform limits

This route does not execute engine workflows.

It exists so future clients can discover API capabilities without hard-coding
the full route and export matrix from documentation.

## `GET /v2/source-formats`

Returns supported and deferred native source-format metadata.

This mirrors the Story Import format matrix.

## `POST /v2/imports/inspect`

Accepts a JSON request containing:

* `source_id`
* `filename`
* `content_base64`
* optional `title`

The API writes the content to a temporary request file, asks Project Manager to import it, and returns bounded source-structure metadata.

Decoded source content is limited to 10 MiB per request. Oversized payloads fail with `413 import_content_too_large` before parsing or storage.

The response includes:

* source ID
* source format
* title
* chapter count and IDs
* scene count and IDs
* scene map
* paragraph count
* evidence-anchor count
* bounded evidence-anchor previews

The response must not include source quote text or full chapter text.

## `POST /v2/extraction-prompts`

Accepts the same source content fields as import inspection:

* `source_id`
* `filename`
* `content_base64`
* optional `title`
* optional `scene_id`

The API imports the source through Project Manager, builds a scene extraction
input, and asks Entity Extraction to build the evidence-bounded prompt.

The response includes:

* source ID
* source format
* selected scene ID
* evidence-anchor count
* extraction prompt

This route intentionally returns prompt text because the prompt is the requested
production artifact. It still must be generated by the extraction layer, not by
API string assembly.

## `POST /v2/extractions/apply`

Accepts source content plus an evidence-bounded AI response payload.

The `ai_response` field may contain either:

* a single-scene extraction payload
* a multi-scene envelope using `{"scenes": ...}`

The API imports the source through Project Manager, applies extraction candidates
through Canon Updating, and returns a summary of accepted and rejected candidate
IDs.

The response includes:

* per-scene candidate counts
* accepted entity count and IDs
* accepted fact count and IDs
* accepted relationship count and IDs
* accepted state-change count and IDs
* rejected candidate IDs

The API does not decide which candidates become canon.

Canon Updating decides.

## `POST /v2/canon/preview`

Accepts source content plus an evidence-bounded AI response payload and returns compact accepted Canon metadata.

This is the Phase 1 Canon API foundation.

The response includes:

* accepted entity counts and IDs
* accepted fact counts and IDs
* accepted relationship counts and IDs
* accepted state-change counts and IDs
* rejected candidate IDs

The API does not own Canon truth.

It only exposes the result of Canon Updating.

## `POST /v2/timeline/preview`

Accepts source content plus an evidence-bounded AI response payload and returns compact Timeline metadata.

This is the Phase 1 Timeline API foundation.

The response includes:

* chapter IDs in story order
* scene map in story order
* current scene ID
* accepted state-change IDs

The API does not determine timeline validity.

It only exposes the story order and state-change metadata produced by the engine workflow.

## `GET /v2/projects`

Returns durable project metadata for the authenticated user.

This is the Phase 6 Project Storage API foundation.

The route requires a bearer session token and `X-Aevryn-Now` header.

It reads through the Project Repository boundary configured by `create_app` or `AEVRYN_PROJECT_DATABASE_PATH`.

It does not read browser storage.

It does not run the engine.

## `POST /v2/projects`

Creates one durable project for the authenticated user.

The request includes:

* `project_id`
* `name`
* `now`

Project names are normalized before storage.

The route writes through the Project Repository boundary configured by `create_app` or `AEVRYN_PROJECT_DATABASE_PATH`.

Duplicate project IDs fail clearly.

## `GET /v2/projects/{project_id}`

Returns one durable project inside the authenticated user's ownership boundary.

Missing projects and cross-user project reads return a stable project-not-found response.

The route must not leak whether another user owns the requested project ID.

## `GET /v2/projects/{project_id}/settings`

Returns durable project settings inside the authenticated user's ownership boundary.

If a project has no saved settings, the repository returns safe defaults:

* `default_export_format`: `markdown`
* `locale`: `en-US`

Missing projects and cross-user project reads return a stable project-not-found response.

## `PUT /v2/projects/{project_id}/settings`

Updates durable project settings inside the authenticated user's ownership boundary.

The request includes:

* `default_export_format`
* `locale`

The API normalizes export format tokens and trims locale values before storage.

Invalid settings fail clearly.

Missing projects and cross-user project writes return a stable project-not-found response.

## `GET /v2/projects/{project_id}/stories`

Returns durable story metadata inside the authenticated user's project boundary.

The route returns story IDs, titles, and timestamps only.

It does not import source files or run the engine.

Missing projects and cross-user project reads return a stable project-not-found response.

## `POST /v2/projects/{project_id}/stories`

Creates durable story metadata inside the authenticated user's project boundary.

The request includes:

* `story_id`
* `title`
* `now`

Story titles are normalized before storage.

Duplicate story IDs fail clearly.

Missing projects and cross-user project writes return a stable project-not-found response.

## `GET /v2/projects/{project_id}/stories/{story_id}/imports`

Returns durable source import metadata inside the authenticated user's story boundary.

The route returns import IDs, source IDs, filenames, source formats, storage references, structure counts, and timestamps only.

It does not return uploaded source prose.

Missing stories, cross-project story reads, and cross-user story reads return a stable story-not-found response.

## `POST /v2/projects/{project_id}/stories/{story_id}/imports`

Inspects source structure through Story Import and persists import metadata inside the authenticated user's story boundary.

The request includes:

* `import_id`
* `source_id`
* `filename`
* `content_base64`
* `title`
* `now`

The route stores metadata and a storage reference, not uploaded source bytes.

Decoded source content is limited to 10 MiB per request. Oversized payloads fail with `413 import_content_too_large` before parsing or storage.

Duplicate import IDs fail clearly.

Missing stories, cross-project story writes, and cross-user story writes return a stable story-not-found response.

## `GET /v2/projects/{project_id}/runs`

Returns durable engine run metadata inside the authenticated user's project boundary.

The route returns run IDs, story/import scope, status, engine version, timestamps, error summaries, and queue references.

It does not execute queued work.

Missing projects and cross-user project reads return a stable project-not-found response.

## `GET /v2/projects/{project_id}/status`

Returns metadata-only project status inside the authenticated user's project boundary.

The route reports project status, latest import, latest engine run, worker/job state, snapshot availability, export availability, latest failure summary, and recent workflow events.

It does not inspect source, execute workers, create snapshots, or return source prose.

Missing projects and cross-user project reads return a stable project-not-found response.

## `GET /v2/projects/{project_id}/snapshots`

Returns persisted engine output snapshots inside the authenticated user's project boundary.

The route returns snapshot IDs, project/story/run scope, snapshot kind, content type, serialized output, and creation timestamp.

It does not create or mutate snapshots.

Missing projects and cross-user project reads return a stable project-not-found response.

## `GET /v2/projects/{project_id}/stories/{story_id}/snapshots`

Returns persisted engine output snapshots inside the authenticated user's story boundary.

The optional `snapshot_kind` query parameter filters by supported snapshot kind.

Invalid snapshot kinds fail clearly with `invalid_snapshot_kind`.

Missing stories, cross-project story reads, and cross-user story reads return a stable story-not-found response.

## `POST /v2/projects/{project_id}/stories/{story_id}/imports/{import_id}/runs`

Submits a saved import for background engine processing.

The request includes:

* `run_id`
* `job_id`
* `now`

The route records a pending engine run and enqueues a background job through the worker boundary.

It does not run the engine inline.

When an import content store and snapshot worker handler are configured, the worker can later generate a deterministic canon snapshot from the saved source bytes.

Duplicate run IDs or job IDs fail clearly.

Missing imports, cross-story imports, cross-project imports, and cross-user imports return a stable import-not-found response.

## `POST /v2/workers/process`

Drains queued background jobs through the worker boundary.

The request includes:

* `started_at`
* `finished_at`
* `max_jobs`

The route returns claimed, succeeded, and failed job counts.

When deployment API keys are configured, this internal workflow route requires `X-Aevryn-API-Key` or an equivalent bearer API key.

The route updates queue status and durable engine run status.

When configured with the import snapshot worker handler, it also persists a deterministic `canon` snapshot for each successfully processed import run.

## `POST /v2/workers/runs/{run_id}/snapshots`

Persists one trusted worker-produced snapshot for a completed run.

The request includes:

* `snapshot_id`
* `snapshot_kind`
* `content_type`
* `serialized_output`
* `now`

Project, story, and run scope are derived from the stored run, not from the request payload.

Snapshots can only attach to succeeded runs.

Invalid snapshot kinds, invalid serialized JSON, incomplete runs, and wrong run scope fail clearly.

Duplicate snapshot IDs fail clearly.

When deployment API keys are configured, this internal workflow route requires `X-Aevryn-API-Key` or an equivalent bearer API key.

## `POST /v2/projects/preview`

Accepts source content plus an evidence-bounded AI response payload and returns stateless project-level metadata.

This route is the Phase 1 Project Management API foundation.

It does not create a persisted project.

It does not write to a database.

It asks Project Manager to run the same import and candidate-application workflow as the CLI, then returns enough metadata for a future frontend to decide what outputs can be requested next.

The response includes:

* source ID
* source format
* title
* chapter IDs
* scene IDs
* current scene ID
* evidence-anchor count
* accepted entity IDs
* accepted fact IDs
* accepted relationship IDs
* accepted state-change IDs
* available output links for direct character, scene, prompt, world, continuity, aggregate output, and export previews
* current platform limits

The response must not include source quote text or full chapter text.

Persistent project creation belongs to the Project Database phase.

## `POST /v2/characters/preview`

Accepts source content plus an evidence-bounded AI response payload and returns timeline-aware character profiles.

This is the Phase 1 Character API foundation.

It asks Project Manager and Character Engine for character state at the requested scene position.

The API does not build character cards itself.

Character profiles expose backend-provided `race` and `gender` sections alongside status, goals, equipment, abilities, assets, territory, relationships, limitations, recent changes, and evidence summary. Unknown identity facts remain `Unknown`; the frontend should not infer them.

## `POST /v2/scenes/preview`

Accepts source content plus an evidence-bounded AI response payload and returns one timeline-aware scene sheet.

This is the Phase 1 Scene API foundation.

It asks Project Manager, Scene Engine, Scene Analyzer, and Presentation Engine for the view model.

The API does not analyze scenes itself.

## `POST /v2/prompts/preview`

Accepts source content plus an evidence-bounded AI response payload and returns one production pack.

This is the Phase 1 Prompt API foundation.

It asks Prompt Engine and Presentation Engine for canon-backed prompt output.

The API does not generate prompts by assembling strings directly.

## `POST /v2/world/preview`

Returns a timeline-aware world sheet for a requested scene.

The route asks Project Manager to run the stateless preview, asks World Engine to reconstruct world state at the requested scene, and asks Presentation Engine to convert that state into a user-facing world sheet.

The API does not reconstruct world state itself and does not return source prose.

## `POST /v2/continuity/preview`

Returns a project-level continuity report split into new, updated, still-known, and invalidated records by scene.

The route asks Project Manager to build the continuity report from accepted Canon update summaries.

The API does not compare source text, infer continuity changes, or mutate Canon.

## `POST /v2/project-outputs/preview`

Accepts source content plus an evidence-bounded AI response payload and returns
stateless platform-ready output views.

This route exists so the website can prove it can consume engine outputs before
the persistent Project Database is added.

The request includes:

* `source_id`
* `filename`
* `content_base64`
* optional `title`
* `ai_response`
* optional `scene_id`
* optional `character_ids`
* optional `world_entity_ids`

The API imports the source, applies extraction candidates through Canon
Updating, reconstructs the requested scene position, and returns:

* character profiles
* scene sheet
* production pack
* world sheet
* continuity report

The response is presentation-ready.

Character profile output must include API-provided `race` and `gender` sections so identity facts are tracked by Canon-backed presentation rather than inferred in the browser.

It must not include full source chapter text by default.

Exact evidence inspection should be exposed later through intentional evidence
controls.

Timeline output must include API-provided `timeline_changes` rows for the latest
canon snapshot. Each row is metadata-only:

* change ID
* chapter index
* scene index
* chapter title
* scene title
* entity ID
* entity display name
* state attribute
* state value

The frontend may group and render these rows, but it must not infer Timeline
state or reconstruct continuity from raw snapshot payloads.

Scene output must include API-provided `scene_sheets` from the latest canon
snapshot. Each sheet is a human-readable scene panel with:

* scene ID
* scene title
* chapter label
* location
* characters present
* mood
* purpose
* visual highlights
* continuity changes
* environment
* evidence summary

For alpha, project output responses may cap the number of rendered scene sheets
to keep large imports usable. The frontend renders the API-provided sheets; it
does not reconstruct scene context from raw Canon or source prose.

Prompt Pack output must include API-provided `prompt_packs` from the latest
canon snapshot. Each prompt pack reuses the production-pack view contract:

* scene
* image prompt
* narration prompt
* camera prompt
* animation prompt

Continuity output must include an API-provided `continuity_report` when the
latest canon snapshot contains continuity records. The report is metadata-only:
it includes record descriptions and evidence IDs, but not source quotes.

Export output must include API-provided `export_options` that describe available
export kinds and formats. Project output summaries must not include full
serialized export content; full export content remains behind explicit export
routes.

## `GET /v2/projects/{project_id}/exports`

Returns generated export metadata inside an authenticated project.

The response includes export IDs, snapshot IDs, export kind, format, filename,
content type, size, checksum, and creation time.

It does not return storage references or serialized export content.

## `POST /v2/projects/{project_id}/exports`

Persists a generated export from a durable snapshot.

The first storage-backed export target is deliberately narrow:

* source: existing project snapshot
* format: JSON
* bytes: written through `StorageService`
* metadata: recorded in the Project Database

The request includes:

* `export_id`
* `snapshot_id`
* `export_format`
* optional `filename`
* `now`

The API does not re-run the engine while creating an export.

## `GET /v2/projects/{project_id}/exports/{export_id}/download`

Downloads generated export bytes after authentication and project ownership
checks.

The frontend never receives R2 credentials or storage references.

## `POST /v2/exports/preview`

Accepts source content plus an evidence-bounded AI response payload and returns
one serialized export preview.

This route proves the frontend can request portable output without owning
serialization.

The request includes:

* `source_id`
* `filename`
* `content_base64`
* optional `title`
* `ai_response`
* `export_kind`
* `export_format`
* optional `scene_id`
* optional `character_ids`
* optional `character_id`
* optional `world_entity_ids`

Supported Phase 1 export previews:

* `character_profile` as Markdown
* `scene_sheet` as Markdown
* `production_pack` as Markdown
* `world_sheet` as Markdown
* `prompt_bundle` as Markdown, JSON, or CSV
* `continuity_report` as Markdown or JSON

The response includes:

* source ID
* source format
* scene ID
* export kind
* export format
* filename
* content type
* serialized content

The API selects the export target.

The Export Engine serializes it.

For API previews, continuity report exports preserve evidence IDs and scene anchors but omit exact evidence quote text. Local engine exports may remain audit-complete.

The frontend never generates export files directly.

---

# Failure Modes

The API can fail if:

* Request JSON is invalid
* Base64 content is invalid
* Source format is unsupported
* Deferred parser formats are supplied
* Story Import rejects the source
* The requested scene is unknown
* Extraction payload shape is invalid
* Canon Updating rejects unsupported candidates
* Requested character or world entity IDs are unknown
* Requested export kind or format is unsupported
* Temporary request file handling fails

Expected workflow errors should return structured API errors instead of tracebacks.

All API errors use the same top-level shape:

```json
{
  "error": "machine_readable_error_code",
  "detail": "Human-readable failure detail."
}
```

Validation errors use:

```json
{
  "error": "invalid_request",
  "detail": "body.source_id: Field required"
}
```

Route-level workflow errors use route-specific codes such as:

* `authentication_required`
* `invalid_api_key`
* `invalid_base64`
* `import_failed`
* `extraction_prompt_failed`
* `extraction_apply_failed`
* `canon_preview_failed`
* `timeline_preview_failed`
* `project_preview_failed`
* `character_preview_failed`
* `scene_preview_failed`
* `prompt_preview_failed`
* `world_preview_failed`
* `continuity_preview_failed`
* `project_output_preview_failed`
* `export_preview_failed`

---

# V2 Rule

The API owns the contract.

The engine owns continuity.

No API route may bypass the engine to create canon, timeline, presentation, or export behavior.
