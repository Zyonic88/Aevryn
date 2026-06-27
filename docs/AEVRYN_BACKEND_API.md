# Aevryn Backend API

> Built by **Aetherra Labs**

This document defines the Version 2 Phase 1 Backend API boundary.

The API is a contract layer.

It is not the engine.

It is not the frontend.

It is not the database.

---

# What Is It?

The Backend API is the stable HTTP contract that platform clients use to access aevryn.

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
* Project Outputs
* Exports

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

* `invalid_base64`
* `import_failed`
* `extraction_prompt_failed`
* `extraction_apply_failed`
* `project_output_preview_failed`
* `export_preview_failed`

---

# V2 Rule

The API owns the contract.

The engine owns continuity.

No API route may bypass the engine to create canon, timeline, presentation, or export behavior.
