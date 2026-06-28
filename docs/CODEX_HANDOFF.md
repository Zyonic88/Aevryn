# Codex Handoff

> Built by **Aetherra Labs**

This document preserves the active project context for future Codex sessions.

Read this file before making code changes.

---

# Project

Name: **Aevryn**

Repository: `https://github.com/Zyonic88/Aevryn`

Primary local path: `C:\Users\enigm\Documents\Aevryn`

Main domain: `Aevryn.ai`

Aevryn was formerly named SceneSmith. Any remaining `SceneSmith` references should be treated as migration leftovers unless they are part of historical test data, old chat logs, or intentionally preserved compatibility text.

---

# Product Purpose

Aevryn is an AI-powered Story Continuity Engine.

Its purpose is to understand existing stories, maintain a living canon, and generate evidence-backed production data for creators.

Aevryn is not a story generator.

Aevryn is not an image generator in V1 or V2.

Aevryn is not a chatbot.

Core philosophy:

**Evidence in. Canon out.**

---

# Current Development Stage

Aevryn V1 engine is complete.

Aevryn is currently in **V2 Platform Development**.

Current phase: **Phase 7 in progress - Import UI hardening**

Recent completed V2 work:

- Phase 1: Backend API
- Phase 2: Project Database
- Phase 3: Background Workers
- Phase 4: Authentication
- Phase 5A: Web Alpha Shell
- Phase 5B: Engine Output Views
- Phase 6: Project Storage
- Import workspace view completed
- Character workspace view completed
- World workspace view completed
- Timeline workspace view completed
- Scene workspace view completed
- Continuity workspace view completed
- Prompt Pack workspace view completed
- Export request UI completed

Phase 5B engine output views are implemented.

Before future frontend polish, read `docs/AEVRYN_UX_ARCHITECTURE.md`. Phase 5 has working API-backed views, but the next frontend experience pass should start with workspace architecture and low-fidelity wireframes, not colors, icons, gradients, or animation.

Next expected V2 target:

- Phase 7 Import UI hardening, governed by `docs/AEVRYN_ROADMAP.md`, `docs/AEVRYN_IMPORT_FORMAT_MATRIX.md`, and `docs/AEVRYN_WEB_IMPORT_SYSTEM.md`

Phase 6 Project Storage accepted:

- Durable project storage API routes added for list/create/detail
- Routes use bearer-session authentication plus the Project Repository boundary
- `create_app_from_env` can wire local JSON project storage from `AEVRYN_PROJECT_DATABASE_PATH`
- `create_app_from_env` wires `JsonAuthenticationStore` from `AEVRYN_AUTH_STORE_PATH` or a sibling `_auth.json` file
- `create_app_from_env` wires `FileSystemImportContentStore` from `AEVRYN_IMPORT_STORAGE_PATH` or a sibling `_imports` directory
- CLI `aevryn api` now uses the environment-backed app factory in reload and non-reload modes
- Dashboard list/create now uses the project storage API instead of browser project shells as source of truth
- Direct workspace project routes load project detail through the API, with legacy local shell fallback only for compatibility
- Project Settings API routes added for read/update and the workspace Settings tab now saves through the API
- Project Story API routes added for list/create and the workspace Story tab now creates story metadata through the API
- Story Import API routes added for list/create metadata and the workspace Import tab now saves inspected import metadata under durable stories
- Engine Run API routes added for list/submit and the workspace Import tab now submits saved imports to the background job boundary
- Worker Process API route added for draining queued jobs and durably moving engine runs through worker lifecycle states
- Snapshot API storage boundary added: authenticated project/story snapshot read routes plus an internal worker route for persisting worker-produced snapshots against succeeded runs
- Import snapshot worker handler added for reading saved import bytes and automatically producing deterministic `canon` snapshots from successful import runs
- Frontend API client now understands project/story snapshot list responses
- Phase 6 exit verification passed: Ruff, mypy, pytest, frontend lint/type/test/build, and Aevryn validation corpus

Phase 6 storage limitation:

- JSON project and auth stores are local deterministic adapters, not final production database or identity-provider choices
- Story import storage now has a local source-byte adapter, but this is not the final production object-storage choice
- Worker execution now produces one deterministic `canon` snapshot from saved import content; richer snapshot families remain later integration slices

Phase 7 starting point:

- Treat Phase 7 as Import UI hardening and supported-format workflow completion, not a from-scratch import UI build
- Verify TXT, Markdown, HTML, FB2, DOCX, ODT, EPUB, Paste Text, and deferred format behavior through the UI/API path
- Keep Web Import experimental and permission-aware until explicitly scoped
- Improve saved import, run, and snapshot visibility in the workspace only where it supports the storage-backed workflow

Phase 7 progress:

- Import workspace now has a source file input that reads selected bytes, derives source IDs from filenames, sends the same `content_base64` API payload as pasted text, and blocks deferred source formats before inspection/save
- Frontend coverage now includes file-upload inspect payloads, byte base64 encoding, filename-derived source IDs, and deferred-format preflight behavior
- Supported upload extensions from the API now populate the browser file picker accept list, and app coverage exercises TXT, Markdown, HTML, FB2, DOCX, ODT, and EPUB through the upload-to-inspect path
- Import workspace now reads story-scoped canon snapshots and labels project runs with snapshot availability after refresh

---

# Development Method

Use **Iron Clad Development**.

For each phase:

1. Plan before code.
2. Build only the phase scope.
3. Harden the phase.
4. Run the relevant checks.
5. Commit and push.
6. Move to the next phase only after the current phase is solid.

Do not rush into later phases.

---

# Engineering Rules

Follow the project rules in:

- `docs/DEVELOPMENT_RULES.md`
- `docs/AEVRYN_V1_ACCEPTANCE_CRITERIA.md`
- `docs/AEVRYN_V2_PHASE_5_ACCEPTANCE.md`
- `docs/AEVRYN_V2_PHASE_6_ACCEPTANCE.md`
- `docs/AEVRYN_PLATFORM_ARCHITECTURE.md`
- `docs/AEVRYN_UX_ARCHITECTURE.md`

Project rules that matter most:

- Architecture before code.
- Single responsibility.
- Type hints everywhere.
- Public classes and public functions need docstrings.
- Tests are required.
- No generated artifacts committed.
- No TODO placeholders for incomplete production behavior.
- No unnecessary complexity.
- Deterministic behavior matters.
- Evidence-backed truth matters.
- Authority boundaries are sacred.

---

# Authority Boundaries

The engine owns continuity.

The API owns the contract.

The frontend owns interaction.

The Presentation Engine owns view models.

The Export Engine owns serialization.

No frontend component may bypass the API.

No API route may bypass the engine.

No system may duplicate another system's authority.

If one system needs another system's data, it asks through the correct boundary.

---

# V1 Feature Boundary

V1 and V1.1 improvements are allowed only when they improve:

- Continuity
- Extraction
- Canon
- Evidence
- Presentation
- Testing
- Translation
- Determinism
- Performance
- Documentation
- Source import support

Do not add V2+ media features to the engine.

---

# V2 Scope

V2 transforms the engine into a usable platform while keeping the engine independent.

V2 includes:

- Backend API
- Project database
- Background workers
- Authentication
- Website
- Project storage
- Import UI
- Monitoring
- Performance
- Internal alpha

V2 does not include:

- Image generation
- Video generation
- Storyboards
- Voice
- Music
- Cloud collaboration
- Payments
- Subscriptions
- Teams
- Publishing pipeline

---

# Frontend Rules

The frontend stack is Vite, React, and TypeScript.

Frontend boundary rules:

- The API client is the only place that knows endpoint paths.
- Components never call `fetch` directly.
- Components never shape backend data into engine meaning.
- Components render API view models and local UI state.
- Engine logic never lives in the frontend.

Frontend views should include:

- Loading states
- Error states
- Empty states
- Auth token handling
- API capability awareness where relevant

---

# Testing And Validation

The project uses deterministic validation heavily.

Important validation concepts:

- Canon Rebuild Test
- Incremental Test
- Out-of-Order Protection Test
- Canon Stability Test
- Cross-genre validation corpus
- Full novel import validation

Known validation corpus includes multiple genres and at least one full novel EPUB test.

Generated outputs should not be committed unless they are explicitly approved golden fixtures.

---

# Local Commands

Use the commands defined by the repository when possible.

Common checks may include:

```powershell
pytest
ruff check .
mypy src
```

For frontend work, inspect the package scripts before running checks:

```powershell
Get-Content package.json
```

Then use the repo's configured scripts for linting, type checking, and tests.

---

# Git Rules

Commit meaningful changes.

Use clear commit messages.

Push after completing and hardening a phase or meaningful subphase.

Do not commit:

- Build outputs
- Caches
- Runtime data
- Generated validation outputs unless intentionally approved
- Local Codex metadata

`.codex/` is ignored intentionally.

---

# Current Workspace Note

The project was renamed from SceneSmith to Aevryn.

If a Codex session still shows `C:\Users\enigm\Documents\SceneSmith`, it is likely an old thread/runtime binding.

Use a fresh Codex session pointed at:

```text
C:\Users\enigm\Documents\Aevryn
```

The active repository should resolve to:

```text
C:/Users/enigm/Documents/Aevryn
```

The GitHub remote should resolve to:

```text
https://github.com/Zyonic88/Aevryn.git
```
