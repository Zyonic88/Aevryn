# Aevryn V2 Phase 1 Acceptance Criteria

> Built by **Aetherra Labs**

This document defines when Version 2 Phase 1, the Backend API, can be considered complete.

Phase 1 is complete only when the API is a stable contract over the existing engine.

The API must remain thin.

It must not become the engine.

---

# Scope

Phase 1 includes:

* REST API application
* OpenAPI contract
* Health and capability discovery
* Source-format discovery
* CORS configuration
* Optional API-key protection for workflow routes
* Import inspection
* Extraction prompt generation
* Extraction candidate application
* Canon preview
* Timeline preview
* Project preview
* Character preview
* Scene preview
* Prompt preview
* World preview
* Continuity preview
* Aggregate project output preview
* Export preview

Phase 1 does not include:

* Persistent project database
* Background workers
* Full user accounts
* Password authentication
* Project permissions
* Website UI
* Cloud storage
* Payments
* Collaboration
* Image generation
* Video generation

---

# Acceptance Checklist

## Contract

* API routes use stable operation IDs.
* API routes use stable tags.
* Public discovery routes are available without workflow authentication.
* Workflow routes can be protected by API key.
* Request and response models are typed and documented.
* Capabilities expose route and export metadata for future clients.
* Project preview links expose direct output routes.

## Engine Boundaries

* API does not own Canon truth.
* API does not own Timeline truth.
* API does not parse stories directly.
* API does not construct Presentation view models directly.
* API does not serialize exports directly.
* API calls Project Manager and engine subsystems for workflow behavior.

## Safety

* Import inspection does not return source prose.
* Presentation preview routes redact exact source prose.
* Continuity report API previews preserve evidence IDs without returning exact source quotes.
* Deferred source formats fail clearly.
* Invalid base64 fails clearly.
* Workflow failures return structured error responses.
* Responses include API identity and request tracing headers.

## CLI Parity

The API must cover the creator-facing CLI workflow:

* `aevryn import` -> `POST /v2/imports/inspect`
* `aevryn extraction-prompt` -> `POST /v2/extraction-prompts`
* `aevryn extract-ai-json` -> `POST /v2/extractions/apply`
* `aevryn character` -> `POST /v2/characters/preview`
* `aevryn scene` -> `POST /v2/scenes/preview`
* `aevryn prompt` -> `POST /v2/prompts/preview`
* `aevryn world` -> `POST /v2/world/preview`
* `aevryn continuity` -> `POST /v2/continuity/preview`

The developer validation workflow remains CLI-only unless a later admin API is deliberately added.

## Verification

Before Phase 1 is declared complete, run:

```powershell
ruff check pyproject.toml src tests
mypy src tests
pytest -q
```

All checks must pass.

---

# Phase Exit Rule

Do not start Phase 2 until Phase 1 has been hardened to the point where remaining improvements are either low-value churn or clearly belong to Phase 2.
