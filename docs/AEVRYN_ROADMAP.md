# Aevryn Development Roadmap

> Built by **Aetherra Labs**

This document defines the long-term development roadmap for aevryn.

The roadmap exists to prevent scope creep and ensure every feature is built in the correct order.

**Rule:**

A feature belongs in the earliest version where it is required.

If a feature is not required for the current version, it must wait.

---

# Current Position

Current active target:

```text
V2 Phase 7
-> Import UI hardening
-> Supported-format workflow completion
```

Phase 6 Project Storage is accepted.

The product path now has durable project identity, storage-backed workspace access, saved imports, queued runs, import source-byte storage, and deterministic `canon` snapshots from successful import runs.

Phase 7 should make the import workflow feel complete and trustworthy before Aevryn moves into monitoring, performance, and internal alpha work.

---

# Version 1 - Story Continuity Engine (Complete)

## Goal

Create the world's most accurate AI-powered Story Continuity Engine.

Version 1 focuses on understanding stories.

It does **not** generate media.

## Feature Freeze

Version 1 is complete and under feature freeze.

Until Version 1 is released, Aevryn must not add:

* New core systems
* New architecture
* Major redesigns

Allowed work:

* Bug fixes
* Performance improvements
* UX improvements
* Testing
* Documentation

The goal from this point forward is release confidence.

---

## Core Systems

* Story Import
* Translation Engine (Foundation Only)
* Entity Extraction
* Canon Updating
* Canon Engine
* Timeline Engine
* Character Engine
* World Engine
* Scene Engine
* Scene Analyzer
* Prompt Engine
* Presentation Engine
* Export Engine
* Project Manager

---

## Core Capabilities

* Import novels
* Import web novels
* Import scripts
* Parse chapters
* Parse scenes
* Build Canon
* Track continuity
* Track world state
* Generate living character cards
* Generate scene summaries
* Generate prompt packs
* Export production-ready data

---

## Deliverables

* Character Cards
* Scene Sheets
* Timeline
* Relationship Graph
* Prompt Packs
* JSON
* Markdown
* CSV

---

## Success Criteria

A creator can upload a story and generate canonically accurate scene information without manually tracking continuity.

---

## Aevryn V1 RC1

Release Candidate 1 is reached when:

* Architecture is frozen
* All V1 systems are complete
* Acceptance criteria pass
* Canon Rebuild Test passes
* 10-chapter continuity test passes
* No known critical bugs remain
* Documentation is complete

RC1 is not a feature milestone.

RC1 is a confidence milestone.

---

# Version 2 - The Platform

## Goal

Transform the Aevryn Engine into a usable product while keeping the engine completely independent.

The website becomes a client of the engine, not the place where the engine lives.

Platform authority boundaries are defined in `docs/AEVRYN_PLATFORM_ARCHITECTURE.md`.

The core architecture becomes:

```text
Website
-> API
-> Aevryn Engine
```

Everything the CLI can do, the API must be able to do.

---

## V2 Phase Status

| Phase | Name | Status | Notes |
| --- | --- | --- | --- |
| 1 | Backend API | Accepted | API contract over engine workflows is in place. |
| 2 | Project Database | Accepted | Persistence boundary, JSON adapter, ownership rules, and records exist. |
| 3 | Background Workers | Accepted | Durable run lifecycle and worker queue boundary exist. |
| 4 | Authentication | Accepted | Register, login, session, and password reset flows exist. |
| 5A | Web Alpha Shell | Accepted | Login, dashboard, routing, shell, and base states exist. |
| 5B | Engine Output Views | Accepted | Workspace output views and API-backed previews exist. |
| 6 | Project Storage | Accepted | Durable project workflows, saved imports, runs, import content storage, and snapshots exist. |
| 7 | Import UI | Next | Harden supported import formats and storage-backed import workflow. |
| 8 | Monitoring | Planned | Observability after product path is measurable. |
| 9 | Performance | Planned | Optimize after monitoring gives real workflow data. |
| 10 | Internal Alpha | Planned | Private alpha after import, monitoring, and performance are stable. |

---

## Phase 1 - Backend API

Status: **Accepted**

Everything goes through the API.

The API boundary is defined in `docs/AEVRYN_BACKEND_API.md`.

Phase 1 completion is governed by `docs/AEVRYN_V2_PHASE_1_ACCEPTANCE.md`.

Systems:

* REST API
* Authentication middleware
* Project management API
* Import API
* Canon API
* Character API
* Scene API
* Timeline API
* Prompt API
* Export API

Deliverable:

```text
Everything the CLI can do
-> The API can do
```

---

## Phase 2 - Project Database

Status: **Accepted**

The database boundary is defined in `docs/AEVRYN_PROJECT_DATABASE.md`.

Phase 2 completion is governed by `docs/AEVRYN_V2_PHASE_2_ACCEPTANCE.md`.

The engine currently works on local projects.

Version 2 adds persistent storage for product use.

Store:

* Users
* Projects
* Stories
* Canon
* Timeline
* Character Cards
* World State
* Exports
* Settings

Recommended database:

* PostgreSQL

---

## Phase 3 - Background Workers

Status: **Accepted**

Never process imports in the browser.

Workflow:

```text
Upload
-> Queue
-> Worker
-> Processing
-> Finished
```

Possible worker systems:

* Redis
* RQ
* Celery
* Dramatiq

---

## Phase 4 - Authentication

Status: **Accepted**

System authority is defined in `docs/AEVRYN_AUTHENTICATION.md`.

Acceptance criteria are defined in `docs/AEVRYN_V2_PHASE_4_ACCEPTANCE.md`.

Keep authentication simple for Version 2.

Required:

* Register
* Login
* Forgot Password
* Projects

Not required:

* Social logins

---

## Phase 5 - Website

Status: **Accepted**

The website boundary is defined in `docs/AEVRYN_WEBSITE.md`.

Workspace UX architecture is defined in `docs/AEVRYN_UX_ARCHITECTURE.md`.

Phase 5 completion is governed by `docs/AEVRYN_V2_PHASE_5_ACCEPTANCE.md`.

The frontend is built after the backend API, storage, workers, and authentication boundaries exist.

Phase 5 is split into two hardening passes.

### Phase 5A - App Shell

Required first:

* Login
* Register
* Dashboard
* Project workspace shell
* Sidebar
* Placeholder workspace tabs
* API health check
* API capabilities check
* Auth token handling
* Basic routing
* Loading states
* Error states
* Empty states

### Phase 5B - Engine Output Views

Required after Phase 5A is hardened:

* Import Story
* Project
* Story
* Characters
* World
* Timeline
* Scenes
* Continuity
* Prompt Packs
* Exports

Character view:

* Portrait Placeholder
* Summary
* Abilities
* Equipment
* Relationships
* History
* Evidence

Scene view:

* Summary
* Mood
* Purpose
* Visual Highlights
* Prompt Pack
* Evidence

World view:

* Locations
* Organizations
* Items
* Vehicles
* Ownership

Timeline view:

```text
Chapter
-> Scene
-> Changes
```

Continuity view:

* New
* Updated
* Invalidated
* Warnings
* Evidence

---

## Phase 6 - Project Storage

Phase 6 completion is governed by `docs/AEVRYN_V2_PHASE_6_ACCEPTANCE.md`.

Status: **Accepted**

Users should never lose work.

Projects contain:

* Imports
* Canon
* Exports
* History
* Snapshots

---

## Phase 7 - Import UI

Status: **Next**

Phase 7 should harden the storage-backed import workflow already started in Phase 5B and Phase 6.

It should not rebuild the import UI from scratch.

Phase 7 owns the creator-facing intake path:

```text
Choose source
-> Inspect source
-> Save import
-> Submit processing
-> See run status
-> See generated snapshot availability
```

The goal is confidence that every supported source type travels through the same API-backed storage workflow without losing evidence anchors or confusing the creator.

Supported import paths:

* TXT
* Markdown
* HTML
* FB2
* DOCX
* ODT
* EPUB
* Paste Text

Phase 7 UI acceptance:

* The import workspace clearly distinguishes paste input, file upload, supported formats, deferred formats, and experimental web import.
* TXT, Markdown, HTML, FB2, DOCX, ODT, and EPUB can be exercised through the UI/API path or have an explicit tested reason they are not exposed yet.
* Deferred PDF, MOBI, and AZW3 inputs fail clearly before users think they are supported.
* Saved imports remain visible after refresh.
* Submitted runs remain visible after refresh.
* Successful runs expose generated snapshot availability.
* Failed runs show stable, non-crashing error states.
* The UI never implies imported source text is generated output.
* React still does not import engine code or bypass the API client.

Web Import:

Web Import remains experimental until permission checks, rate limits, and source attribution are production-safe.

Phase 7 may include a URL intake placeholder, metadata preview, or permission-checking design, but it must not add unrestricted fetching.

Parser-backed future import paths:

* PDF
* MOBI
* AZW3

---

## Phase 8 - Monitoring

Status: **Planned**

Every meaningful workflow must be observable.

Log:

* Every import
* Every extraction
* Every failure
* Every export

---

## Phase 9 - Performance

Status: **Planned**

Optimize after the product path is measurable.

Measure:

* Import Time
* Canon Time
* Scene Time
* Prompt Time
* Export Time
* Memory

---

## Phase 10 - Internal Alpha

Status: **Planned**

Version 2 ends with a private alpha, not a public launch.

Use it.

Break it.

Fix it.

---

## Version 2 Success Criteria

A creator can:

```text
Register
-> Create Project
-> Upload Novel
-> Wait
-> View Character Cards
-> View World
-> View Timeline
-> View Scene Sheets
-> View Prompt Packs
-> Export
```

without touching the CLI.

---

## What Is Not Version 2

Version 2 does not include:

* Image Generation
* Video Generation
* Storyboards
* Voice
* Music
* Cloud Collaboration
* Payments
* Subscriptions
* Teams
* Publishing

Those belong to Version 3 or later.

---

# Version 3 - Production Expansion

## Goal

Extend the platform beyond continuity workflows into media generation, collaboration, monetization, and publishing.

Version 3 begins only after the Version 2 platform lets creators use Aevryn without touching the CLI.

---

## Candidate Systems

* Image Generation Engine
* Image Consistency Engine
* Character Reference Engine
* Environment Reference Engine
* Style Library
* Asset Manager
* Video Generation Engine
* Storyboard Engine
* Shot Planner
* Camera Director
* Timeline Composer
* Audio Synchronization
* Voice Pipeline
* Music Pipeline
* Publishing Engine
* Payments
* Subscriptions
* Teams
* Cloud Collaboration

---

## Version 3 Rule

The Canon Engine remains the source of truth.

No production, collaboration, or monetization system may replace Canon.

---

# Future Versions

## Goal

Future versions should be split only after Version 2 reaches internal alpha and Version 3 scope is deliberately reviewed.

Do not schedule additional major versions while the platform foundation is still unproven.

---

# Long-Term Vision

Aevryn is not simply an AI prompt generator.

Aevryn is a Story Continuity Platform.

Its purpose is to understand stories so creators can produce consistent, high-quality AI-assisted media without manually tracking canon.

The Canon Engine will always remain the foundation of every future capability.

Every future system must consume Canon.

No future system may replace Canon.
