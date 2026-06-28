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

Optional explicit authentication store path:

```text
AEVRYN_AUTH_STORE_PATH=C:\Users\enigm\Documents\Aevryn\.local\auth_store.json
```

If `AEVRYN_AUTH_STORE_PATH` is omitted, Aevryn stores local auth records beside the project database using the project database filename plus `_auth.json`.

When this value is present, `create_app_from_env` wires:

* `JsonProjectRepository` for local Project Database records
* `AuthenticationService` over the same repository for user ownership records
* `JsonAuthenticationStore` for credential hashes, session token hashes, and password reset token hashes

This means local project records, credential hashes, session token hashes, and password reset token hashes survive process restarts.

The JSON auth store is a deterministic local adapter, not the final production identity provider.

If `AEVRYN_PROJECT_DATABASE_PATH` is absent, authenticated project routes fail clearly with `project_storage_unavailable` instead of silently creating stateless project shells.

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
```

These headers appear on successful responses and structured error responses.

They exist so clients, logs, and future platform tooling can identify the API
contract version without parsing response bodies.

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

Returns API health metadata.

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

It must not include full source chapter text by default.

Exact evidence inspection should be exposed later through intentional evidence
controls.

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
