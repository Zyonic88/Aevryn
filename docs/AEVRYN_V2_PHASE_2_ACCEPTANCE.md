# Aevryn V2 Phase 2 Acceptance Criteria

> Built by **Aetherra Labs**

This document defines when Version 2 Phase 2, the Project Database, can be considered complete.

Phase 2 is complete only when Aevryn has a durable persistence boundary for platform projects.

The database must remain a storage layer.

It must not become the engine.

---

# Scope

Phase 2 includes:

* Project Database architecture
* Persistence data models
* Repository interfaces
* Project ownership records
* Story records
* Import metadata records
* Engine run records
* Snapshot records
* Export records
* Settings records
* Storage reference fields
* Migration or schema strategy
* Schema manifest
* Snapshot payload validation
* Deterministic repository tests

Phase 2 does not include:

* Background workers
* Job execution queues
* Full registration and login flows
* Password recovery
* Website UI
* Cloud file storage implementation
* Payments
* Collaboration
* Image generation
* Video generation

---

# Acceptance Checklist

## Architecture

* Project Database purpose is documented.
* Canon Database and Project Database boundaries are documented.
* Storage vs database responsibilities are documented.
* PostgreSQL remains the production target.
* A schema manifest defines the logical Phase 2 table, constraint, and index contract.
* Schema statements produce a deterministic digest for migration review.
* Schema table order rejects forward references that would break inline foreign keys.
* Local testing strategy is deterministic.
* Local durable persistence is available without weakening the PostgreSQL production target.

## Data Model

* Users can be represented for future ownership.
* Projects can be created and retrieved.
* Stories can be attached to projects.
* Imports can be attached to stories.
* Engine runs can be recorded.
* Engine run lifecycle states reject impossible combinations.
* Engine runs only reference imports from the same story.
* Engine run status transitions move forward only.
* Engine run timestamps cannot move backward.
* Engine run updates cannot change project, story, or import scope.
* Snapshots can be stored immutably.
* Snapshots can be read by story and filtered by snapshot kind without crossing ownership boundaries.
* Snapshots can only be stored for succeeded engine runs.
* JSON snapshots reject malformed serialized output.
* Exports can reference snapshots and storage locations.
* Export kind must match the snapshot kind being serialized.
* Settings can be stored without overriding engine rules.

## Repository Boundary

* API code does not write raw SQL directly.
* Engine code does not know about platform persistence.
* Repository methods are typed.
* Repository methods have clear failure modes.
* Duplicate records fail clearly.
* Missing records fail clearly.
* Cross-user or cross-project access is rejected by repository policy where applicable.

## Determinism

* Saving and loading a project preserves stable IDs.
* Saving and loading snapshots preserves serialized engine output.
* Repeated reads return equivalent data.
* Local persisted records can be reloaded through a fresh repository instance.
* Partial or unknown local JSON sections fail clearly during repository load.
* Corrupted local uniqueness, ownership, and relationship graphs fail clearly during repository load.
* Failed local writes roll back in-memory state.
* Snapshot history is append-only unless an explicit delete/archive operation is implemented.

## Safety

* Uploaded file bytes are not stored directly in structured database records.
* Export file bytes are not stored directly in structured database records.
* Storage references are explicit, use machine-readable schemes, and reject parent-directory traversal.
* Filename metadata cannot smuggle filesystem paths.
* Audit timestamps must parse as valid UTC timestamp strings ending in `Z`.
* Persistence failures do not silently fall back to stateless previews.

## Verification

Before Phase 2 is declared complete, run:

```powershell
ruff check pyproject.toml src tests
mypy src tests
pytest -q
```

All checks must pass.

---

# Phase Exit Rule

Do not start Phase 3 until Phase 2 has been hardened to the point where remaining improvements are either low-value churn or clearly belong to Phase 3.
