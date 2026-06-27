# Aevryn Platform Architecture

> Built by **Aetherra Labs**

This document defines the Version 2 platform architecture before platform code is written.

Version 1 proved the engine.

Version 2 must prove the platform without weakening the engine.

---

# Core Rule

The website is a client of the engine.

The website is not where the engine lives.

The platform exists to make the Aevryn Engine usable through a product interface while preserving the engine's independence, determinism, evidence rules, and authority boundaries.

---

# Core Philosophy

Aevryn is not a website.

Aevryn is a story production workspace.

The website is the interface users interact with.

The engine remains the product.

---

# Golden Rule

The website never owns story logic.

The engine owns story logic.

The website presents engine results.

---

# Platform Flow

```text
Browser
-> Frontend Workspace
-> Platform API
-> Authentication
-> Project Manager
-> Aevryn Engine
-> Database / Storage
```

Every production workflow must follow this path.

No UI may bypass the API.

No API may bypass the engine.

---

# Workspace Philosophy

Aevryn should feel like an IDE, not a traditional website.

Users should feel as though they are opening a project, not browsing pages.

The experience should take product inspiration from:

* Visual Studio Code
* JetBrains IDEs
* Obsidian

The workflow should emphasize productivity, navigation, and continuity rather than page transitions.

---

# Navigation Philosophy

Navigation is persistent.

The left sidebar is always visible.

Users should never lose their place.

Navigation reflects the engine architecture.

It is not an arbitrary menu.

## V2 Sidebar

* Story
* Characters
* World
* Timeline
* Scenes
* Continuity
* Prompt Packs
* Exports
* Settings

Future versions may expand this list.

The navigation grows.

It never fundamentally changes.

---

# Premium Modules

Future premium features should not be hidden.

Instead they should appear as locked modules.

Examples:

* Image Generation
* Video Generation
* Storyboards
* Voice Generation
* Music Generation

Hovering over a locked module should explain what the feature does and which tier includes it.

This keeps users aware of future capabilities without making the interface feel incomplete.

---

# Workspace Layout

The Version 2 workspace should use a stable production-tool layout:

```text
Aevryn                                              Active Project
---------------------------------------------------------------------
Sidebar        | Tabs
               |-----------------------------------------------------
Story          |
Characters     |
World          | Main Workspace
Timeline       |
Scenes         |
Continuity     |
Prompt Packs   |
Exports        |
Settings       |
---------------------------------------------------------------------
Locked Modules | Validation | Logs | Queue | Output
```

The layout should stay stable while the active workspace tab changes.

---

# Tabs

The workspace is tab-based.

Users may open multiple project views at the same time:

* Character
* Scene
* Timeline
* Prompt Pack
* Continuity Report

Tabs remember their state.

Closing a tab never loses project information.

Project data remains owned by the platform and engine layers, not by a transient browser tab.

---

# Workspace Views

The center workspace changes based on the selected tab.

## Character View

* Summary
* Abilities
* Equipment
* Relationships
* Timeline
* Evidence

## Scene View

* Summary
* Purpose
* Mood
* Characters
* Environment
* Prompt Pack

## Timeline View

* Interactive story progress
* Changes
* Events
* Evidence

Each view should answer one creator question quickly.

---

# Right Inspector

The right inspector is a future optional panel for advanced context.

Examples:

* Evidence
* Confidence
* Linked entities
* Timeline position
* Warnings
* Validation

The panel may be collapsed.

---

# Bottom Panel

The bottom panel displays operational information:

* Validation
* Import queue
* Logs
* Warnings
* Processing
* Output

This mirrors the workflow of professional IDEs.

---

# Project Tree

Projects should be navigable like structured source workspaces:

```text
Story
  Chapter 1
  Chapter 2
Characters
  Zhao Chen
  Charlotte
World
  Blizzard Zero
Timeline
Scenes
```

This mirrors how Aevryn internally understands stories.

---

# Global Search

Global search should always be available.

Users should be able to locate:

* Characters
* Scenes
* Locations
* Items
* Evidence
* Relationships
* Timeline events
* Prompt packs

Search should feel similar to "Go to Anything" in a professional IDE.

---

# Platform Engineering Rules

## The Website Never Owns Business Logic

The website may render, collect input, and guide interaction.

It must not decide canon truth, timeline validity, evidence acceptance, extraction rules, prompt rules, export formats, or project state transitions.

## The API Owns the Contract

The API defines how clients interact with aevryn.

It owns request and response shapes, authentication enforcement, permission checks, error responses, rate limits, and versioned platform contracts.

## The Engine Owns Continuity

The Aevryn Engine remains responsible for story import, evidence, extraction candidate handling, canon updating, canon state, timeline state, character cards, world state, scene context, scene analysis, prompt packs, presentation view models, and export serialization.

## The Frontend Owns Interaction

The frontend owns workspace navigation, tabs, forms, loading states, empty states, error display, filtering, sorting controls, visual layout, and user workflow ergonomics.

## Presentation Engine Owns View Models

Frontend components render view models prepared by the Presentation Engine.

The frontend must not reconstruct character cards, scene sheets, world sheets, continuity reports, or prompt packs from raw canon data.

## Export Engine Owns Serialization

The Export Engine owns JSON, Markdown, CSV, and future portable output formats.

The API may deliver serialized output.

The frontend may request downloads.

Neither the API nor the frontend may reinvent export formatting.

---

# Authority Boundaries

## Browser

## What Is It?

The user's runtime environment.

## Why Does It Exist?

It lets creators access Aevryn without touching the CLI.

## What Authority Does It Own?

* User session storage permitted by the platform
* Local UI state
* File selection before upload

## What Does It Not Own?

* Canon truth
* Business logic
* Project persistence
* Authentication decisions
* Export generation

## How Does It Fail?

* Network loss
* Expired sessions
* Unsupported files
* Browser storage limits

## How Does It Interact With Other Systems?

The browser loads the frontend and sends requests to the API through frontend code.

---

## Frontend

## What Is It?

The web client that renders Aevryn workflows.

## Why Does It Exist?

It makes the proven engine usable by creators.

## What Authority Does It Own?

* Interaction design
* Page routing
* UI state
* Form state
* Loading states
* Error presentation
* Rendering API responses

## What Does It Not Own?

* Canon rules
* Timeline rules
* Evidence validation
* AI extraction rules
* Project persistence
* Export serialization
* Permission decisions

## How Does It Fail?

* API unavailable
* Invalid client state
* Upload interruption
* Stale data
* Rendering errors

## How Does It Interact With Other Systems?

The frontend calls the API and renders API responses. It never calls engine internals directly.

Every frontend action must map to an API call.

If a workflow cannot be expressed through the API, the architecture should be reconsidered.

---

## API

## What Is It?

The platform contract between clients and the Aevryn Engine.

The Phase 1 API contract is documented in `docs/AEVRYN_BACKEND_API.md`.

## Why Does It Exist?

It gives the website and future clients one stable, authenticated way to use aevryn.

## What Authority Does It Own?

* REST endpoints
* Request validation
* Response contracts
* Authentication enforcement
* Authorization checks
* API errors
* Rate limits
* Job submission
* Platform contract versioning

## What Does It Not Own?

* Canon truth
* Story analysis rules
* Presentation view construction
* Export serialization
* Background job execution logic

## How Does It Fail?

* Invalid requests
* Unauthorized access
* Forbidden project access
* Missing resources
* Engine errors
* Worker queue failures
* Database failures

## How Does It Interact With Other Systems?

The API authenticates requests, validates permissions, calls Project Manager or job queues, and returns stable responses.

---

## Authentication

## What Is It?

The platform identity and access boundary.

## Why Does It Exist?

It protects user projects and ensures each request belongs to an authorized user.

## What Authority Does It Own?

* Registration
* Login
* Password reset
* Sessions or tokens
* User identity
* Project access checks

## What Does It Not Own?

* Engine behavior
* Canon truth
* Project content interpretation
* UI rendering

## How Does It Fail?

* Invalid credentials
* Expired sessions
* Unauthorized requests
* Permission mismatches
* Account recovery failures

## How Does It Interact With Other Systems?

Authentication gates API requests before project or engine work is allowed.

---

## Project Manager

## What Is It?

The orchestration layer that coordinates Aevryn engine workflows for a project.

## Why Does It Exist?

It keeps API handlers thin and prevents clients from stitching engine subsystems together themselves.

## What Authority Does It Own?

* Workflow orchestration
* Project-level engine calls
* Import-to-output coordination
* Job result coordination

## What Does It Not Own?

* Canon truth
* Timeline truth
* Presentation formatting
* Export serialization
* Authentication policy

## How Does It Fail?

* Missing project data
* Invalid workflow order
* Engine validation errors
* Job result mismatch

## How Does It Interact With Other Systems?

The API asks Project Manager to perform platform workflows. Project Manager asks engine subsystems to do their owned work.

---

## Aevryn Engine

## What Is It?

The independent continuity engine proven in Version 1.

## Why Does It Exist?

It owns evidence-backed story continuity.

## What Authority Does It Own?

* Story Import
* Evidence anchors
* Entity Extraction boundaries
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

## What Does It Not Own?

* User accounts
* Web sessions
* HTTP contracts
* Browser interaction
* Payment handling
* Cloud collaboration

## How Does It Fail?

* Invalid source input
* Invalid evidence references
* Invalid extraction payloads
* Canon conflicts
* Timeline conflicts
* Export format errors

## How Does It Interact With Other Systems?

Project Manager invokes the engine through stable interfaces. The engine returns deterministic outputs, view models, serialized exports, and validation errors.

---

## Database

## What Is It?

The persistent structured storage layer for platform data.

## Why Does It Exist?

Users should never lose work.

## What Authority Does It Own?

* Persisted users
* Persisted projects
* Persisted stories
* Persisted canon data
* Persisted timeline data
* Persisted settings
* Job records
* Export records

## What Does It Not Own?

* Canon validation
* Timeline interpretation
* Business logic
* UI rendering
* File blob storage

## How Does It Fail?

* Connection failures
* Migration failures
* Constraint violations
* Transaction conflicts
* Backup or restore issues

## How Does It Interact With Other Systems?

The API and worker processes read and write database records through repository or persistence interfaces.

---

## Storage

## What Is It?

The blob storage layer for files that should not live directly in the database.

## Why Does It Exist?

Imported files, generated exports, and snapshots may be too large or too file-like for relational rows.

## What Authority Does It Own?

* Uploaded source files
* Export files
* Validation snapshots
* Project snapshots

## What Does It Not Own?

* Canon truth
* Searchable project metadata
* Permission rules
* Export generation

## How Does It Fail?

* Missing files
* Permission failures
* Corrupt uploads
* Quota limits
* Slow downloads

## How Does It Interact With Other Systems?

The API and workers store and retrieve files by stable storage references. Database records point to storage objects when needed.

---

# Engine Relationship

The frontend never constructs story state.

It requests data.

The engine provides:

* Character cards
* Scene context
* World state
* Timeline
* Continuity
* Prompt packs
* Presentation views

The frontend renders those results.

---

# Presentation Relationship

The Presentation Engine prepares view models.

The frontend renders them.

Presentation never belongs in frontend business logic.

---

# Export Relationship

The Export Engine writes portable output.

The frontend never generates exports directly.

---

# Module Philosophy

Future capabilities should be modular.

Examples:

* Image Generation
* Video Generation
* Storyboards
* Voice Generation
* Publishing

These modules consume the engine.

They never replace it.

---

# UX Principles

The interface should answer one question per view.

Examples:

* Who is this character?
* What changed in this scene?
* Where is this location?
* What happened in this chapter?
* What prompt should I use?

If a user cannot answer the active view's question within a few seconds, the interface should be simplified.

---

# Design Principles

Keep whitespace generous.

Avoid clutter.

Avoid unnecessary animation.

Favor readability over decoration.

Professional tools prioritize clarity.

---

# Engineering Principles

The UI mirrors the engine.

Navigation mirrors engine architecture.

Backend preserves truth.

Frontend presents clarity.

The engine is always the source of truth.

No UI component owns Canon.

No UI component owns Timeline.

No UI component owns Continuity.

No UI component bypasses the API.

No API bypasses the engine.

---

# V2 Build Discipline

Build the platform in the same order that made Version 1 work:

```text
Make it work.
Make it reliable.
Make it pleasant.
```

Do not begin with visual polish.

Do not put engine logic in the website.

Do not put UI formatting in the API.

Do not let persistence become business logic.

The platform is trustworthy only if every layer respects its authority boundary.

---

# Long-Term Vision

Aevryn is a browser-based production workspace.

Users should feel like they are sitting inside the project's brain.

Everything they see is a live view of the deterministic continuity engine underneath.

The workspace should disappear into the background, allowing creators to focus entirely on their stories.
