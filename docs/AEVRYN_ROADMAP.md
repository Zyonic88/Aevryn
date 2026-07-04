# Aevryn Development Roadmap

> Built by **Aetherra Labs**

This document defines the long-term development roadmap for aevryn.

The roadmap exists to prevent scope creep and ensure every feature is built in the correct order.

Future ideas are preserved separately in `docs/AEVRYN_FUTURE_IDEAS.md`.

**Rule:**

A feature belongs in the earliest version where it is required.

If a feature is not required for the current version, it must wait.

---

# Current Position

Current active target:

```text
V2 Platform
-> Product development complete for private/internal alpha
-> Next: V2 Release Candidate Readiness
```

Phase 6 Project Storage is accepted.

Phase 7 Import UI is accepted.

Phase 8 Monitoring is accepted.

Phase 9 Performance is accepted.

Phase 10 Internal Alpha is accepted for internal operator testing with documented limitations.

Phase 11 Security & Privacy Hardening is accepted as the V2 trust gate. Public beta remains blocked by deployment-specific production decisions documented in the Phase 11 security docs.

V2 closeout is recorded in `docs/AEVRYN_V2_CLOSEOUT.md`.

V2 Release Candidate Readiness is defined in `docs/AEVRYN_V2_RELEASE_CANDIDATE_READINESS.md`.

The product path now has durable project identity, storage-backed workspace access, saved imports, queued runs, import source-byte storage, deterministic `canon` snapshots from successful import runs, supported-format import UI hardening, metadata-only workflow observability, performance budgets, metadata-only baseline artifacts, regression comparison, and workspace-load request hardening.

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
| 7 | Import UI | Accepted | Supported import formats, deferred-format failures, refresh visibility, snapshots, failed runs, and Web Import boundary are hardened. |
| 8 | Monitoring | Accepted | Metadata-only project status, workflow observability, health/storage status, and restrained monitoring UI exist. |
| 9 | Performance | Accepted | Budgets, baseline measurements, regression checks, and measured optimizations are in place. |
| 10 | Internal Alpha | Accepted | Internal alpha path is ready with documented limitations. |
| 11 | Security & Privacy Hardening | Accepted | Trust-gate docs, tests, scans, deletion/privacy boundaries, and hardening gates are complete; public beta still requires deployment-specific security decisions. |
| 12 | Language And Identity Understanding | Active | Translation Foundation and Entity Resolution Foundation are now required V2 quality gates before release-candidate readiness can close. |

V2 platform product development was previously closed for private/internal alpha. Hosted alpha evidence has reopened V2 for two required story-understanding gates: Translation Foundation and Entity Resolution Foundation.

The active product work track is Phase 12. V2 Release Candidate Readiness remains blocked until Phase 12 is accepted.

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

Status: **Accepted**

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

Status: **Accepted**

Every meaningful workflow must be observable.

Log:

* Every import
* Every extraction
* Every failure
* Every export

Phase 8 completion is governed by `docs/AEVRYN_V2_PHASE_8_ACCEPTANCE.md`.

Accepted monitoring scope:

* `GET /v2/projects/{project_id}/status` reports metadata-only project status inside the authenticated project boundary.
* Project status reports latest import, latest engine run, worker/job state, snapshot availability, export availability, latest failure summary, and recent workflow events.
* API health reports metadata-only project and import storage adapter availability.
* Preview and extraction workflows emit metadata-only success and failure logs with stable workflow kinds and error codes.
* The frontend Monitoring tab displays API health, current project run state, latest failure, snapshot/export availability, storage availability, and recent workflow events from API-provided data.
* Monitoring observes workflows; it does not execute workflows.

---

## Phase 9 - Performance

Status: **Accepted**

Optimize after the product path is measurable.

Measure:

* Import Time
* Canon Time
* Scene Time
* Prompt Time
* Export Time
* Memory

Phase 9 completion is governed by `docs/AEVRYN_V2_PHASE_9_ACCEPTANCE.md`.

Core rule:

```text
Measure.
Budget.
Detect regressions.
Optimize only where measured.
```

Phase 9 optimizes latency for the single-user V2 product path. Throughput, horizontal scaling, distributed workers, production database tuning, cache infrastructure, and cloud autoscaling belong later.

Accepted performance scope:

* `docs/AEVRYN_PERFORMANCE.md` defines budgets, metadata-only measurements, regression snapshots, and the Phase 9 optimization log.
* `aevryn performance-baseline` generates ignored metadata-only baseline artifacts.
* Baseline measurements cover import inspect, import save, worker processing, snapshot creation, project status, workspace load, export preview, and validation suite.
* `aevryn performance-baseline --compare-to <baseline.json>` reports warning and critical regressions while failing only on critical regressions.
* Frontend workspace-load hardening avoids immediate duplicate API health fetches during dashboard-to-monitoring navigation.
* Phase 9 does not include throughput optimization, production infrastructure, cache infrastructure, cloud scaling, new admin consoles, or broad frontend redesign.

---

## Phase 10 - Internal Alpha

Status: **Accepted For Internal Alpha**

Version 2 ends with an internal alpha, not a public launch.

Use it.

Break it.

Fix it.

Phase 10 completion is governed by `docs/AEVRYN_V2_PHASE_10_ACCEPTANCE.md`.

Internal alpha readiness is defined in `docs/AEVRYN_INTERNAL_ALPHA.md`.

Phase 10 includes recovery as a first-class readiness concern: after refresh, session expiry, worker interruption, failed runs, or network/API interruption, the question is whether the user can continue.

Phase 10 readiness should be versioned through Smoke Test, Integration Test, Operational Readiness Test, and Release Candidate Test gates.

Current alpha status:

* Automated backend and frontend gates are passing.
* Manual alpha testing has validated import, processing, monitoring, refresh recovery, and processed-output review for Characters, World, Timeline, and Scenes.
* Processed Continuity, Prompt Packs, and Exports panels now consume persisted backend snapshot output at the API/frontend contract level.
* Browser sanity testing validated Continuity, Prompt Packs, and Exports against persisted backend snapshots.
* Internal alpha operator instructions are documented in `docs/AEVRYN_PRIVATE_ALPHA_TESTER_GUIDE.md`.
* Phase 10 is closed as an internal alpha gate only; outside testers and public beta require deployment-specific follow-through on the accepted Phase 11 security and privacy contracts.

---

## Phase 11 - Security & Privacy Hardening

Status: **Accepted**

Security is architecture.

Privacy is product integrity.

Phase 11 happens after internal alpha and before public beta.

Phase 11 completion is governed by `docs/AEVRYN_V2_PHASE_11_ACCEPTANCE.md`.

Security architecture is defined in `docs/AEVRYN_SECURITY.md`.

Privacy architecture is defined in `docs/AEVRYN_PRIVACY.md`.

API security hardening is defined in `docs/AEVRYN_API_SECURITY_HARDENING.md`.

Audit ledger architecture is defined in `docs/AEVRYN_AUDIT_LEDGER.md`.

Repository secret scanning is defined in `docs/AEVRYN_REPOSITORY_SECRET_SCAN.md`.

Dependency auditing is defined in `docs/AEVRYN_DEPENDENCY_AUDIT.md`.

Static security scanning is defined in `docs/AEVRYN_STATIC_SECURITY_SCAN.md`.

Backup retention boundaries are defined in `docs/AEVRYN_BACKUP_RETENTION.md`.

User-facing trust principles are defined in `docs/AEVRYN_TRUST_MODEL.md` and `docs/AEVRYN_USER_RIGHTS.md`.

Content classification is defined in `docs/AEVRYN_CONTENT_CLASSIFICATION.md`.

Public-launch legal drafts are tracked in `docs/TERMS_OF_SERVICE.md`, `docs/PRIVACY_POLICY.md`, `docs/ACCEPTABLE_USE_POLICY.md`, and `docs/SECURITY_DISCLOSURE.md`.

Data retention and recovery engineering policy drafts are tracked in `docs/DATA_RETENTION_POLICY.md` and `docs/BACKUP_AND_RECOVERY.md`.

Repeatable security gates are tracked in `docs/AEVRYN_PHASE_11_SECURITY_GATES.md`.

Phase 11 gates are complete. The security gate tracker currently lists no remaining Phase 11 implementation gates.

Opening slice:

* Verify authorization boundaries across every owned project surface.
* Prove cross-user project, story, import, run, snapshot, export/status, settings, output, and deletion access fails closed.
* Keep all security diagnostics metadata-only and free of source prose, full AI payloads, serialized export content, credentials, tokens, and storage references.

Phase 11 includes:

* identity hardening
* authorization boundary verification
* story privacy
* data protection
* encryption decisions
* API hardening
* deletion verification
* backup and recovery privacy
* audit logging
* security headers
* rate limiting strategy
* request and upload validation
* secrets management
* dependency auditing
* repository secret scanning
* static security scanning
* production fail-closed configuration

Phase 11 acceptance does not mean public beta is ready by itself. Public beta still requires production-specific decisions for identity provider, database/storage adapters, secret manager, object storage, backup retention windows, audit storage, rate limiting, HTTPS/HSTS edge policy, hosted dependency and secret scanning, branch protection, and provider retention terms.

Core privacy rule:

```text
Your stories are yours.
Aevryn is built to understand them, not to own them.
```

Phase 11 must make these statements technically true:

* Uploaded stories belong to the creator.
* Generated canon belongs to the creator.
* Generated exports belong to the creator.
* Aetherra Labs does not claim ownership of uploaded manuscripts.
* Aetherra Labs does not train on user stories without explicit opt-in.
* Deleted stories are removed from Aevryn-owned active storage.

Phase 11 does not include new product features, public launch, payments, collaboration, publishing, image generation, video generation, chatbot behavior, or broad frontend redesign.

---

## Phase 12 - Language And Identity Understanding

Status: **Active**

Phase 12 completion is governed by `docs/AEVRYN_V2_PHASE_12_ACCEPTANCE.md`.

Phase 12 promotes two story-understanding systems into required V2 scope:

* Translation Foundation
* Entity Resolution Foundation

Core rule:

```text
Translation preserves meaning.
Resolution preserves identity.
Canon decides truth.
```

Translation Foundation is defined in `docs/AEVRYN_TRANSLATION_ENGINE.md`.

Entity Resolution is defined in `docs/AEVRYN_ENTITY_RESOLUTION.md`.

Phase 12 exists because alpha testing showed that Aevryn can import and process chapters, but long-form accuracy depends on correctly preserving language meaning and entity identity across aliases, titles, descriptions, pronouns, scenes, and chapters.

Phase 12 does not add media generation, publishing, payments, collaboration, broad frontend redesign, or a public translation product.

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

Status:

```text
Blocked pending Phase 12 acceptance.
```

Public beta remains blocked by Phase 12, production deployment, security, legal, and operating decisions listed in `docs/AEVRYN_V2_CLOSEOUT.md`.

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
