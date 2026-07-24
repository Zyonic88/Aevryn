# Aevryn Website

> Built by **Aetherra Labs**

This document defines the Version 2 Website boundary.

Workspace UX architecture is defined in `docs/AEVRYN_UX_ARCHITECTURE.md`.

Phase-specific acceptance remains governed by:

* `docs/AEVRYN_V2_PHASE_5_ACCEPTANCE.md`
* `docs/AEVRYN_V2_PHASE_7_ACCEPTANCE.md`
* `docs/AEVRYN_V2_PHASE_8_ACCEPTANCE.md`
* `docs/AEVRYN_V2_PHASE_9_ACCEPTANCE.md`
* `docs/AEVRYN_V2_PHASE_10_ACCEPTANCE.md`

---

# Purpose

The Aevryn Website is the browser client for the platform API.

It exists to make Aevryn usable without touching the CLI while keeping the engine completely independent.

---

# What Is It?

The website is a frontend application.

It owns interaction, navigation, browser state, loading states, error states, and rendering API view models.

It does not own business logic.

The website is currently in private internal-alpha hardening. It should become more trustworthy and usable without broad redesign or public-launch scope.

---

# Why Does It Exist?

Version 1 proved the engine.

Version 2 proves the platform.

Creators need a clear app shell where they can authenticate, choose a project, reach import flows, and eventually view character cards, world state, scene sheets, continuity reports, prompt packs, and exports.

---

# Authority Owned

The Website owns:

* Browser routing
* Login and registration screens
* Auth token storage in the browser
* Dashboard interaction
* Project workspace shell interaction
* Sidebar and tab navigation
* Loading, empty, and error states
* API client calls
* Rendering API response contracts
* Creator-facing copy for frontend states
* Local form state needed to prepare API requests
* Explicit browser recovery states after refresh, login, or interrupted navigation

---

# Authority Not Owned

The Website does not own:

* Canon truth
* Story Import parsing
* Entity Extraction
* Background job execution
* Authentication policy
* Project persistence rules
* Presentation view model construction
* Export serialization
* Payments
* Collaboration
* Image generation
* Video generation
* Workflow execution
* Monitoring state inference
* Performance measurement authority

---

# Core Rule

The frontend owns interaction.

The API owns contracts.

The engine owns continuity.

No UI may bypass the API.

No UI may duplicate engine rules.

The frontend API client is the only frontend layer that may know concrete endpoint paths.

Components never call `fetch` directly.

Components never shape backend data into engine meaning.

Monitoring observes workflows. It does not execute workflows.

Frontend workspace views display API-provided workflow state. They do not infer pending, running, succeeded, failed, snapshot, export, or worker state from local assumptions.

The UI may prepare request payloads, but the API owns all durable identities, persistence rules, run lifecycle rules, snapshot availability, and failure contracts.

No website surface may expose full source prose, full AI responses, generated export payloads, credentials, bearer tokens, machine-local paths, or diagnostic payload dumps.

---

# Current Website Shape

The current website includes:

* Login and registration.
* Dashboard with API health and project listing.
* Project creation and project opening.
* Project workspace shell.
* Story metadata creation.
* Import workspace.
* API-backed output workspaces for characters, world, timeline, scenes, continuity, prompt packs, and exports.
* Settings workspace.
* Explicit Monitoring view for diagnostics.

The default workspace navigation should stay creator-focused. Monitoring should remain available only through an explicit action or route, not as everyday workspace noise.

---

# Import Workspace Rules

The Import workspace is the main internal-alpha intake path.

Required behavior:

* Source text starts blank.
* Paste input remains available for manual source text.
* File upload supports single-file intake.
* Multi-file upload supports bundled text-like chapter intake.
* TXT, Markdown, HTML, FB2, DOCX, ODT, and EPUB are exposed only through API-supported paths.
* Deferred formats are blocked before inspection with API-owned format guidance.
* Web Import remains unavailable until permission checks, attribution, rate limits, and safety boundaries are scoped.
* Inspect Import calls the Import API and renders API-provided structure metadata.
* Save Import writes durable story import metadata through the API.
* Submit Processing submits a saved import through the background job boundary.
* Duplicate processing submissions are blocked in the UI and rejected by the API.
* Failed processing remains retryable.

The Import workspace must not:

* Seed misleading source text.
* Keep stale inspected structure after a new source selection starts.
* Reuse an import reference for a newly selected source or bundle.
* Display long filenames as creator-facing status noise.
* Display machine identifiers unless the user opens an explicit advanced/developer affordance.
* Present imported source text as generated output.

---

# Monitoring Rules

Monitoring exists for trust and recovery, not daily creation.

The Monitoring view may display:

* API health.
* Current project run state.
* Latest failure summary.
* Snapshot and export availability.
* Storage adapter availability.
* Recent workflow events.

Monitoring must use only API-provided status data.

Monitoring must not:

* Execute workflows.
* Drain workers.
* Submit imports.
* Infer backend state from frontend cache.
* Become a broad admin console during private alpha.

---

# Output Workspace Rules

Character, World, Timeline, Scene, Continuity, Prompt Pack, and Export workspaces render processed project outputs from API contracts.

Before a canon snapshot exists, these views should explain whether output is unavailable or processing is underway.

After a canon snapshot exists, these views should summarize the API-provided output without exposing full source prose or raw snapshot payloads.

Technical review panels may remain behind explicit disclosure controls while alpha hardening continues.

---

# Phase 5 Historical Split

## Phase 5A - App Shell

Phase 5A proved the frontend architecture.

Accepted scope:

* Vite
* React
* TypeScript
* React Router
* TanStack Query
* Zod
* Vitest
* React Testing Library
* ESLint
* Prettier
* Login screen
* Register screen
* Auth token handling
* Dashboard
* Project workspace shell
* Sidebar
* Placeholder workspace tabs
* API health check
* API capabilities check
* Loading, error, and empty states

Not required at that time:

* Full import processing UI
* Character cards
* World views
* Timeline views
* Scene views
* Prompt packs
* Exports
* Website polish pass

## Phase 5B - Engine Output Views

Phase 5B exposed API-backed engine outputs.

Accepted scope:

* Import UI
* Paste-source inspection through the Import API
* Source-format discovery through the API
* Import structure results rendered from API view models
* UTF-8 source payload preparation before API submission
* Visible source text size guard for pasted imports
* Import result totals and scene preview rows
* Import API failures shown through accessible alerts
* Stale import structure results cleared before follow-up inspections
* Character view
* Character profile previews through the Character API
* Character profile sections rendered from API view models
* Character preview input validates AI response JSON before submission
* Character preview errors and empty states are visible and accessible
* Failed follow-up character previews clear stale profile results
* World view
* World sheet previews through the World API
* World entity sections rendered from API view models
* World preview input validates AI response JSON before submission
* World preview errors and empty states are visible and accessible
* Failed follow-up world previews clear stale world sheet results
* Timeline view
* Timeline previews through the Timeline API
* Timeline scene order and state-change IDs rendered from API metadata
* Timeline preview input validates AI response JSON before submission
* Timeline preview errors and empty states are visible and accessible
* Failed follow-up timeline previews clear stale timeline results
* Scene view
* Scene sheet previews through the Scene API
* Scene sheet sections rendered from API view models
* Scene preview input validates AI response JSON before submission
* Scene preview errors and empty states are visible and accessible
* Failed follow-up scene previews clear stale scene sheet results
* Continuity view
* Continuity previews through the Continuity API
* Continuity scene buckets rendered from API view models
* Continuity preview input validates AI response JSON before submission
* Continuity preview errors and empty states are visible and accessible
* Failed follow-up continuity previews clear stale continuity report results
* Prompt Pack view
* Prompt Pack previews through the Prompt API
* Production pack sections rendered from API view models
* Prompt Pack preview input validates AI response JSON before submission
* Prompt Pack preview errors and empty prompt sections are visible and accessible
* Failed follow-up Prompt Pack previews clear stale production pack results
* Export request UI
* Export previews through the Export API
* Export kind and format options match supported API preview combinations
* Export preview payloads preserve UTF-8 source text and selected output IDs
* Serialized export content, filename, and content type render from API responses
* Export preview input validates AI response JSON before submission
* Export preview errors are visible and accessible
* Failed follow-up export previews clear stale serialized content

---

# Internal Alpha Milestone

Aevryn Internal Alpha.

Acceptance:

* User can register
* User can log in
* Auth token is stored and reused
* Expired stored sessions are rejected
* Dashboard loads
* API health and capabilities display correctly
* User can create and open a project shell
* Workspace sidebar renders
* Workspace tabs open and recover after refresh
* Story/import workflow can be completed without the CLI
* Saved imports survive refresh
* Background runs are observable
* Successful runs produce canon snapshots
* Output views render API-backed processed summaries
* Export preview remains API-backed
* Monitoring remains restrained and explicit
* Recovery checks explain whether the user can continue
* Loading states exist
* Error states exist
* Empty states exist
* No engine logic exists in the frontend
* Frontend tests, lint, type checks, and build pass
* Backend gates still pass

No engine logic lives in the frontend.

---

# Failure Modes

The Website can fail if:

* API base URL is missing or wrong
* API health request fails
* API capabilities request fails
* Authentication requests fail
* Authentication form input is invalid
* Session token is missing, invalid, or expired
* A route is unknown
* An authenticated user opens a public-only auth route
* A project route references a missing project shell
* A workspace tab route is unknown
* Browser storage is unavailable or rejects reads/writes
* Session persistence fails after successful authentication
* API response shape changes
* API returns invalid JSON
* Browser project storage is malformed
* Project shell names are blank
* A workspace tab ID is unknown
* A selected source file cannot be read
* A multi-file source bundle contains unsupported file types
* Import inspection fails
* Import save fails
* Import processing is already active
* A worker is queued, interrupted, failed, or unavailable
* A snapshot is missing after a run
* A user refreshes during import or processing

Failures must be visible to the user, exposed through accessible alerts where appropriate, and testable. Browser storage failures must never crash the shell; when project persistence fails, the project shell may remain usable for the current session with a visible warning.

---

# V2 Website Rule

The website makes the platform usable in a browser.

Do not build:

* Engine logic in React
* Payments
* Collaboration
* Social login
* Image generation
* Video generation
* Production media pipelines
* Broad public-launch marketing pages outside the release-readiness trust, legal, privacy, support, and security surface
* Chatbot behavior
* Broad redesigns during private-alpha hardening
