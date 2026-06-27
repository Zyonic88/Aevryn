# Aevryn Project Database

> Built by **Aetherra Labs**

This document defines the Version 2 Project Database boundary.

The Project Database is platform persistence.

It is not the Canon Engine.

It is not the in-memory Canon Database used by the engine.

It is not blob storage.

---

# What Is It?

The Project Database is the persistent structured storage layer for Aevryn platform projects.

It stores the records needed for users to leave the application, return later, and continue working without losing project state.

---

# Why Does It Exist?

Version 1 proved the engine through local, stateless workflows.

Version 2 needs durable project state.

Creators must be able to:

```text
Create Project
-> Import Story
-> Process Canon
-> Return Later
-> Continue From Saved State
```

without re-running everything manually.

---

# What Authority Does It Own?

The Project Database owns persisted platform records:

* Users
* Projects
* Stories
* Imports
* Imported source metadata
* Engine run records
* Canon snapshots
* Timeline snapshots
* Character card snapshots
* World state snapshots
* Scene sheet snapshots
* Prompt pack snapshots
* Continuity report snapshots
* Export records
* Settings
* Job references
* Storage references
* Audit timestamps using valid UTC timestamp strings ending in `Z`

---

# What Does It NOT Own?

The Project Database does not own:

* Canon truth decisions
* Evidence validation
* Timeline interpretation
* Entity extraction
* Character card construction
* World state reconstruction
* Scene analysis
* Prompt generation
* Presentation view construction
* Export serialization
* User interface behavior
* Background job execution
* Uploaded file bytes
* Generated export file bytes

The database stores records.

The engine creates truth.

---

# Core Rule

The Project Database stores engine outputs.

It does not reinterpret them.

If persisted Canon differs from what the engine produced, the persistence layer is wrong.

---

# Canon Database vs Project Database

Aevryn has two different database concepts.

## Canon Database

The Canon Database is an engine component.

It owns evidence-backed canon storage and lookup during an engine run.

It answers questions like:

* What facts are active at this scene?
* What relationships exist at this chapter?
* What changed in this timeline position?

## Project Database

The Project Database is a platform component.

It owns durable storage for projects and saved engine outputs.

It answers questions like:

* Which projects belong to this user?
* Which imports belong to this story?
* Which engine run produced this snapshot?
* Where is this export stored?

These responsibilities must not be mixed.

---

# Logical Data Areas

## Users

Stores platform identity records required for project ownership. User email values are unique platform identifiers for future authentication flows.

Phase 2 may define the user table shape before full authentication is implemented.

Full registration, login, and password recovery belong to Phase 4.

## Projects

Stores creator workspaces.

A project groups stories, imports, processing runs, snapshots, settings, and exports.

## Stories

Stores story-level metadata inside a project.

A project may eventually contain more than one story, but Phase 2 should keep the model simple.

## Imports

Stores source import metadata.

The database stores references and metadata, not raw uploaded files. Import reads must remain inside project ownership boundaries.

Uploaded files belong to Storage.

## Engine Runs

Stores records of engine processing attempts.

This includes status, timestamps, input references, output snapshot references, and error summaries. Engine run history reads must remain inside project ownership boundaries.

Engine run records may be updated as processing moves from pending or running into succeeded or failed, but updates must not change project, story, or import scope. An engine run may only reference an import from the same story.

Background execution belongs to Phase 3, but the database schema should be ready to reference jobs.

## Snapshots

Stores saved engine output records.

Snapshots are immutable by default.

If a project is reprocessed, a new snapshot is created instead of mutating old output history. Snapshot reads must remain inside project ownership boundaries, support story-scoped lookup, and support deterministic filtering by snapshot kind.

## Exports

Stores export metadata.

Export file bytes belong to Storage.

The database stores filename, content type, export kind, format, source snapshot, and storage reference. Export reads must remain inside project ownership boundaries.

## Settings

Stores project-level and user-level settings.

Settings must not replace engine rules.

---

# Storage Boundary

Large or file-like content should not live directly in the Project Database.

Examples:

* Uploaded source files
* Generated export files
* Large validation snapshots
* Future media assets

The database should store stable storage references for those files. Storage references must use explicit `scheme://path` notation with machine-readable schemes.

---

# Failure Modes

The Project Database can fail if:

* A connection cannot be opened
* A migration is missing or invalid
* A required record does not exist
* A uniqueness constraint is violated
* A transaction conflicts
* A project belongs to a different user
* A snapshot references missing storage
* Serialized engine output is malformed
* A write partially fails

Failures must be explicit.

Silent fallback to stateless behavior is not allowed in platform persistence code.

---

# Determinism Rule

Given the same saved project records and the same engine version, Aevryn must reconstruct the same persisted view models.

If persistence changes the output, persistence is corrupting the product.

---

# V2 Phase 2 Rule

Phase 2 builds persistence foundations only.

Do not build:

* Background workers
* Full authentication flows
* Website UI
* Payments
* Collaboration
* Image generation
* Video generation

---

# Schema Manifest

Phase 2 defines a logical schema manifest in `src/aevryn/persistence/schema.py`.

The manifest records table names, primary keys, references, and storage-oriented column intent before a production database adapter is introduced. It also validates that every declared reference points to an existing table and column.

It is not a migration runner yet.

It can render deterministic PostgreSQL table, check-constraint, and index statements for review and produce a schema digest for migration review.

Those statements are the contract that future PostgreSQL migrations must satisfy. Check constraints preserve core database invariants such as nonnegative import counts, valid engine run statuses, and valid snapshot kinds.

# Snapshot Integrity

Snapshots store serialized engine outputs.

For `application/json` snapshots, serialized output must be valid JSON before it is accepted by persistence models.

The database may store JSON snapshots as PostgreSQL `jsonb`, but persistence code must still preserve the original engine meaning and stable IDs.

---

# Recommended Implementation Direction

Production target:

* PostgreSQL

Development and tests may use deterministic local adapters if they do not weaken the production schema boundary. The JSON repository is a local durability adapter for development and validation, not the production PostgreSQL adapter. Local persisted records must include every required section and pass uniqueness, ownership, and relationship validation when reloaded. Failed local writes must roll back in-memory state instead of leaving the repository half-mutated.

Repository code should depend on interfaces and data models, not on route handlers or frontend assumptions.
