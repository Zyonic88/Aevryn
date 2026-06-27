# Aevryn V2 Phase 6 Acceptance Criteria

> Built by **Aetherra Labs**

This document defines when Version 2 Phase 6, Project Storage, can be considered complete.

Phase 6 makes project work durable for product use.

It must use the existing Project Database boundary instead of creating a second persistence model in the frontend.

---

# Goal

Users should never lose work.

A creator must be able to:

```text
Log in
-> Create Project
-> Leave
-> Return
-> See the same project from API-backed storage
```

without relying on browser-only project shells.

---

# Relationship To Earlier Phases

## Phase 2

Phase 2 built the persistence foundation:

* persistence models
* repository protocol
* ownership rules
* in-memory repository
* deterministic JSON repository
* schema manifest
* story records
* import records
* engine run records
* snapshots
* exports
* settings

Phase 6 must integrate those foundations into platform workflows.

Phase 6 does not redefine the Project Database.

## Phase 5

Phase 5 built the browser client:

* login
* register
* dashboard
* browser project shells
* workspace routing
* API-backed output previews

Phase 6 replaces browser-only project shells with API-backed project storage.

Phase 6 does not add engine logic to React.

## UX Architecture

Workspace UX architecture is defined in `docs/AEVRYN_UX_ARCHITECTURE.md`.

Phase 6 should support the future workspace model, but it should not turn into a visual polish phase.

Durable project data comes first.

---

# Scope

Phase 6 includes:

* API-backed project creation
* API-backed project listing
* API-backed project detail loading
* authenticated ownership boundaries for project reads and writes
* replacement of browser-only project shells as the source of truth
* graceful migration/fallback behavior for existing local browser project shells
* storage-backed workspace routing
* project settings read/write through the API if settings are exposed
* deterministic tests for persistence-backed project workflows
* frontend tests for API-backed project dashboard and workspace entry
* clear failures when persistence is unavailable

Phase 6 may include:

* story metadata creation
* first saved story per project
* project settings surface
* a low-fidelity Story view wireframe
* a low-fidelity Settings view wireframe

These are implementable if they directly support storage-backed project workflows.

Phase 6 does not include:

* visual branding pass
* dark theme polish
* animations
* icon pass
* drag-reorderable tabs
* split panes
* command palette
* global search
* media generation
* collaboration
* payments
* production PostgreSQL deployment

Those are bonus unless explicitly promoted into a scoped phase.

---

# Authority Boundaries

The Project Database owns durable project records.

The API owns project storage contracts.

The frontend owns interaction and navigation.

The engine owns story truth.

Phase 6 must preserve these rules:

* React does not write directly to persistence adapters.
* React does not import `src/aevryn`.
* React does not decide ownership.
* API routes do not bypass repository interfaces.
* Engine code does not know about platform persistence.
* Browser storage is not the project source of truth.
* Persistence failures do not silently fall back to stateless previews.

---

# API Acceptance

Project storage API is accepted when:

* Authenticated users can create a project through the API.
* Authenticated users can list only their own projects.
* Authenticated users can load only their own project details.
* Missing projects return a stable not-found error.
* Cross-user access returns a stable access-denied or not-found response without leaking project data.
* Duplicate or invalid project records fail clearly.
* Project names are normalized consistently with platform rules.
* API responses expose stable project IDs, names, ownership-safe metadata, and update timestamps.
* API code depends on the repository protocol, not concrete storage internals.
* API tests cover persistence success and failure cases.

Minimum route shape should be decided before implementation.

Recommended first routes:

```text
GET  /v2/projects
POST /v2/projects
GET  /v2/projects/{project_id}
```

Optional later routes:

```text
GET  /v2/projects/{project_id}/stories
POST /v2/projects/{project_id}/stories
GET  /v2/projects/{project_id}/settings
PUT  /v2/projects/{project_id}/settings
```

---

# Frontend Acceptance

Frontend storage integration is accepted when:

* Dashboard loads projects from the API after login.
* Dashboard no longer treats `localStorage` project shells as the source of truth.
* Project creation calls the API.
* Project creation shows loading, success, and error states.
* Project creation keeps the dashboard usable if the API request fails.
* Project workspace routes load project details from the API.
* Missing or inaccessible project routes redirect or render a stable error state.
* Direct project workspace URLs work after a browser refresh.
* Auth failures clear or reject project requests predictably.
* Existing local browser project shells do not crash the app.
* Browser storage remains limited to auth/session and harmless local UI state.

---

# Workspace UX Acceptance

Phase 6 must prepare for the workspace architecture without implementing every future panel.

Accepted Phase 6 workspace behavior:

* The Project Workspace loads from durable project metadata.
* The active workspace route answers one primary question.
* Browser refresh does not lose the active project.
* The workspace sidebar remains stable.
* Workspace tabs remain URL-addressable.
* Story and Settings are planned as storage-backed surfaces, even if implemented as low-fidelity placeholders first.

Not required in Phase 6:

* top document tabs
* right info panel
* bottom utility panel
* split panes
* pinned tabs
* tab drag/drop
* search
* command palette
* high-fidelity theme

Those belong after storage-backed project workflows are stable.

---

# Data Acceptance

Project storage data is accepted when:

* Project records use stable machine-readable IDs.
* Project timestamps are valid UTC strings ending in `Z`.
* Project records preserve owner user IDs.
* Project names are human-readable and nonblank.
* Repository reads are deterministic.
* JSON repository reload preserves project records.
* In-memory repository remains usable for isolated tests.
* Persistence adapters reject malformed records.
* Persistence adapters reject invalid ownership graphs.

---

# Migration And Compatibility

Phase 5 used browser-only project shells.

Phase 6 must decide what happens to those shells.

Acceptable options:

* ignore local shells after API-backed storage exists
* show a one-time nonblocking notice
* offer import/migration later

Do not silently merge browser project shells into server projects.

Do not create server records without explicit user action.

---

# Failure Modes

Phase 6 must handle:

* project API unavailable
* project list request fails
* project creation request fails
* project detail request fails
* auth session expires during project requests
* repository raises duplicate record
* repository raises missing record
* repository raises access denied
* repository raises persistence failure
* API response shape changes
* browser refresh on direct workspace URL

Failures must be visible, testable, and must not crash the shell.

---

# Tests Required

Backend tests:

* create project through API
* list projects through API
* load project detail through API
* reject unauthenticated project requests
* reject cross-user project reads
* normalize and validate project names
* surface repository persistence failures
* preserve deterministic project ordering

Frontend tests:

* dashboard loads API projects
* dashboard renders project API loading state
* dashboard renders project API error state
* dashboard creates projects through API
* dashboard does not depend on browser project storage as source of truth
* direct workspace URL loads API project details
* inaccessible project route fails predictably
* project creation failure keeps dashboard usable

Boundary tests:

* no frontend direct `fetch` outside API client
* no frontend imports from `src/aevryn`
* API project routes use repository boundary
* persistence failures do not silently become stateless previews

---

# Verification

Before Phase 6 is declared complete, run:

```powershell
ruff check pyproject.toml docs src tests validation
mypy src tests
pytest -q
npm.cmd run lint
npx.cmd tsc -p tsconfig.json --noEmit
npm.cmd test
npm.cmd run build
python -m aevryn.cli validate --summary-only --source-root "C:\Users\enigm\Desktop\Aevryn test chapters"
```

All checks must pass.

---

# Phase Exit Rule

Do not move beyond Phase 6 until project identity and dashboard/workspace project access are API-backed, durable, tested, and hardened.

Further UX improvements are allowed only when they support durable storage-backed workflows. Otherwise they belong to a later frontend polish phase.
