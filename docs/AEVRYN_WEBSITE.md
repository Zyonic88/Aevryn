# Aevryn Website

> Built by **Aetherra Labs**

This document defines the Version 2 Phase 5 Website boundary.

---

# Purpose

The Aevryn Website is the browser client for the platform API.

It exists to make Aevryn usable without touching the CLI while keeping the engine completely independent.

---

# What Is It?

The website is a frontend application.

It owns interaction, navigation, browser state, loading states, error states, and rendering API view models.

It does not own business logic.

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

---

# Phase 5 Split

## Phase 5A - App Shell

Phase 5A proves the frontend architecture.

Required:

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

Not required:

* Full import processing UI
* Character cards
* World views
* Timeline views
* Scene views
* Prompt packs
* Exports
* Website polish pass

## Phase 5B - Engine Output Views

Phase 5B exposes API-backed engine outputs.

Required later:

* Import UI
* Paste-source inspection through the Import API
* Source-format discovery through the API
* Import structure results rendered from API view models
* UTF-8 source payload preparation before API submission
* Visible source text size guard for pasted imports
* Import result totals and scene preview summaries
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
* Export request UI

---

# First Milestone

Aevryn Web Alpha Shell.

Acceptance:

* User can register
* User can log in
* Auth token is stored and reused
* Expired stored sessions are rejected
* Dashboard loads
* API health and capabilities display correctly
* User can create and open a project shell
* Workspace sidebar renders
* Placeholder tabs open and close
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

Failures must be visible to the user, exposed through accessible alerts where appropriate, and testable. Browser storage failures must never crash the shell; when project persistence fails, the project shell may remain usable for the current session with a visible warning.

---

# V2 Phase 5 Rule

Phase 5 builds the browser client.

Do not build:

* Engine logic in React
* Payments
* Collaboration
* Social login
* Image generation
* Video generation
* Production media pipelines
