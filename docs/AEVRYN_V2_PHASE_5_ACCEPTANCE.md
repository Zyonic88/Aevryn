# Aevryn V2 Phase 5 Acceptance Criteria

> Built by **Aetherra Labs**

This document defines when Version 2 Phase 5, the Website, can be considered complete.

---

# Goal

Create a usable web client for Aevryn without moving platform or engine logic into the browser.

---

# Phase 5A - Aevryn Web Alpha Shell Acceptance

Phase 5A locks the first website milestone: Aevryn Web Alpha Shell.

Aevryn Web Alpha Shell is accepted when:

* User can register
* User can log in
* Auth token is stored and reused
* Expired stored sessions are rejected
* Dashboard loads
* API health and capabilities display correctly
* User can create and open a project shell
* Workspace sidebar renders
* Placeholder tabs open and close
* Loading states exist and use accessible status messages
* Error states exist
* Empty states exist
* No engine logic exists in the frontend
* Frontend tests, lint, type checks, and build pass
* Backend gates still pass

## Frontend Stack

* Vite is configured
* React is configured
* TypeScript is configured
* React Router is configured
* TanStack Query is configured
* Zod validates API responses
* Vitest is configured
* React Testing Library is configured
* ESLint is configured
* Prettier is configured

## Authentication UI

* User can reach login screen
* User can reach register screen
* Authenticated users are redirected away from login and register screens
* Login input is normalized before Auth API calls
* Register input is normalized before Auth API calls
* Register form mirrors the backend password policy for early user feedback
* Login calls the Auth API
* Register calls the Auth API
* Session token is stored through one auth boundary
* Expired sessions are removed through the auth boundary
* Logout clears the session token
* Logout returns the user to login
* Auth API failures render accessible error alerts
* Auth session persistence failures render accessible shell alerts
* Auth failures render visible errors

## Dashboard

* Authenticated user can see dashboard
* Dashboard shows API health state
* Dashboard shows API capabilities state
* Dashboard API failures render accessible error alerts
* Empty project state is visible
* User can create a placeholder project shell
* Blank project names are rejected
* Project names are normalized
* Malformed project storage is handled safely
* Browser storage failures are handled without crashing the shell
* User can open a project shell

## Workspace Shell

* Workspace route exists
* Unknown routes redirect predictably
* Public-only auth routes redirect authenticated users predictably
* Missing project shells redirect predictably
* Direct workspace tab URLs open predictably
* Workspace sidebar exists
* Placeholder tabs exist for Overview, Import, Characters, World, Timeline, Scenes, Continuity, Prompt Packs, and Exports
* Active workspace tabs expose `aria-current`
* Unknown workspace tabs show a stable empty state
* No engine output view is built in Phase 5A

## API Client

* API base URL is centralized
* Auth token handling is centralized
* API errors are normalized
* Network failures are normalized
* Invalid JSON responses are normalized
* API response validation is centralized
* Unexpected API response shapes fail clearly
* Frontend API client is the only frontend layer that knows endpoint paths
* Components never call `fetch` directly
* Components never shape backend data into engine meaning
* Frontend does not call engine modules directly

---

# Phase 5B - Engine Output View Acceptance

Phase 5B begins only after Phase 5A is hardened.

Phase 5B accepts API-backed engine output views one slice at a time. The Import inspection view and Character output view are now implemented as the first slices.

Required later:

* Import UI
* Import UI displays supported and deferred source formats from the API
* Import UI can inspect pasted source text through `/v2/imports/inspect`
* Import UI renders chapter, scene, paragraph, and evidence-anchor counts
* Import UI does not parse source text in React
* Import payload construction preserves UTF-8 source text
* Import payload construction is covered by unit tests
* Import UI shows source text character count and blocks oversized pasted submissions
* Import results summarize totals and clearly label truncated scene previews
* Import UI renders source-format and inspection API failures as accessible alerts
* Deferred source-format failures do not render stale import structure results
* Failed follow-up inspections clear previous successful import results
* Character output view
* Character view calls `/v2/characters/preview` through the API client
* Character view renders API character profile view models
* Character preview payload construction preserves UTF-8 source text
* Character preview payload construction validates AI response JSON before submission
* Character view does not reconstruct Canon, Timeline, or Presentation data in React
* Character view shows invalid AI JSON as a visible form error
* Character view renders empty profile responses as an empty state
* Failed follow-up character previews clear previous successful profile results
* World output view
* World view calls `/v2/world/preview` through the API client
* World view renders API world sheet view models
* World preview payload construction preserves UTF-8 source text
* World preview payload construction validates AI response JSON before submission
* World view does not reconstruct Canon, Timeline, or Presentation data in React
* World view shows invalid AI JSON as a visible form error
* World view renders empty world sections as an empty state
* Failed follow-up world previews clear previous successful world sheet results
* Timeline output view
* Scene output view
* Continuity output view
* Prompt Pack output view
* Export request UI

---

# Tests Required

* App shell renders
* Login form calls auth boundary
* Login form rejects invalid email and blank password before API calls
* Register form calls auth boundary
* Register form rejects invalid email, blank display name, and weak passwords before API calls
* Dashboard renders accessible loading, error, and empty states
* Project shell navigation works
* API client validates health and capabilities responses
* API client normalizes network, invalid JSON, and invalid response-shape failures
* Auth session storage works
* Logout clears stored auth session
* Expired auth sessions redirect to login
* Project shell storage validates malformed browser data
* Browser storage read/write failures do not crash auth or project shell flows
* Auth persistence failure keeps the current tab usable and warns the user
* Frontend has no direct imports from `src/aevryn`
* Frontend has no direct `fetch` calls outside the API client
* Frontend endpoint paths stay inside the API layer

---

# Phase 5A Complete Means

Phase 5A is complete when:

* Frontend lint passes
* Frontend type checks pass
* Frontend tests pass
* Backend tests still pass
* Website docs are complete
* App shell can be run locally
* Remaining work is engine output views, not shell architecture

