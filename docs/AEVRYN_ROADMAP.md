# Aevryn Development Roadmap

> Built by **Aetherra Labs**

This document defines the long-term development roadmap for aevryn.

The roadmap exists to prevent scope creep and ensure every feature is built in the correct order.

**Rule:**

A feature belongs in the earliest version where it is required.

If a feature is not required for the current version, it must wait.

---

# Version 1 - Story Continuity Engine (Current)

## Goal

Create the world's most accurate AI-powered Story Continuity Engine.

Version 1 focuses on understanding stories.

It does **not** generate media.

## Feature Freeze

Version 1 is under feature freeze.

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

## Phase 1 - Backend API

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

The frontend is built after the backend API, storage, workers, and authentication boundaries exist.

Required views:

* Dashboard
* Projects
* Recent Activity
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

Users should never lose work.

Projects contain:

* Imports
* Canon
* Exports
* History
* Snapshots

---

## Phase 7 - Import UI

Supported import paths:

* TXT
* Markdown
* HTML
* FB2
* DOCX
* ODT
* EPUB
* Paste Text
* Web Import

Web Import remains experimental until permission checks, rate limits, and source attribution are production-safe.

Parser-backed future import paths:

* PDF
* MOBI
* AZW3

---

## Phase 8 - Monitoring

Every meaningful workflow must be observable.

Log:

* Every import
* Every extraction
* Every failure
* Every export

---

## Phase 9 - Performance

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

