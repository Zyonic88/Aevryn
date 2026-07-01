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

Current phase: **V2 product complete for private/internal alpha - Release Candidate Readiness next**

Recent completed V2 work:

- Phase 1: Backend API
- Phase 2: Project Database
- Phase 3: Background Workers
- Phase 4: Authentication
- Phase 5A: Web Alpha Shell
- Phase 5B: Engine Output Views
- Phase 6: Project Storage
- Phase 7: Import UI
- Phase 8: Monitoring
- Phase 9: Performance
- Phase 10: Internal Alpha
- Phase 11: Security & Privacy Hardening
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

Future ideas are preserved in `docs/AEVRYN_FUTURE_IDEAS.md`. That document is not the roadmap and should not be treated as implementation scope unless the roadmap is explicitly updated.

Next expected V2 target:

- Work V2 Release Candidate Readiness from `docs/AEVRYN_V2_RELEASE_CANDIDATE_READINESS.md`.
- Gate 1 Public-Facing Trust Documentation is tracked in `docs/AEVRYN_PUBLIC_TRUST_READINESS.md`.
- Public support/contact readiness is tracked in `docs/AEVRYN_PUBLIC_SUPPORT_READINESS.md`.
- Production infrastructure readiness is tracked in `docs/AEVRYN_PRODUCTION_INFRASTRUCTURE_READINESS.md`.
- Proposed production infrastructure decisions are tracked in `docs/AEVRYN_PRODUCTION_INFRASTRUCTURE_DECISIONS.md`.
- Security operations readiness is tracked in `docs/AEVRYN_SECURITY_OPERATIONS_READINESS.md`.
- Security alert routing is tracked in `docs/AEVRYN_SECURITY_ALERT_ROUTING.md`.
- Backup, recovery, and audit readiness is tracked in `docs/AEVRYN_BACKUP_RECOVERY_AUDIT_READINESS.md`.
- AI provider and data-use readiness is tracked in `docs/AEVRYN_AI_PROVIDER_DATA_USE_READINESS.md`.
- Release candidate test readiness is tracked in `docs/AEVRYN_RELEASE_CANDIDATE_TEST_READINESS.md`.
- Use `docs/AEVRYN_V2_CLOSEOUT.md` as the decision record that separates V2 product completion from public beta approval.
- Do not treat Phase 11 acceptance as public beta approval; public beta still requires deployment-specific security decisions and production infrastructure choices.
- Release Candidate Readiness progress: local production startup contract now passes with `startup_contract=ready` and `secrets_printed=0`; hosted CI/security workflows exist under `.github/workflows/`; GitHub branch protection, push protection, and protected-path verification are configured/exercised; hosted alert routing runbook is documented; synthetic GitHub-hosted alert path was tested through issue #10; email inbox receipt from GitHub notification settings remains unverified; a 2026-07-01 local smoke attempt verified fail-closed behavior when production-like environment variables were absent; 2026-07-01 local production-style smoke passed for production config, PostgreSQL Project Database, and Cloudflare R2; smoke evidence is recorded in `docs/AEVRYN_PRODUCTION_LIKE_SMOKE_RECORD.md`; hosted production-like browser/API smoke and release-candidate signoff remain open.
- Branch protection readiness is documented in `docs/AEVRYN_BRANCH_PROTECTION.md` and `docs/AEVRYN_GITHUB_HOSTED_CONTROLS.md`; workflows, CODEOWNERS, Dependabot configuration, GitHub security policy, and pull request template exist in `.github/`. GitHub branch protection is configured for `master` with required pull requests, code-owner review, required checks, up-to-date branches, conversation resolution, and restricted deletions. GitHub dependency graph, Dependabot alerts, Dependabot security updates, secret scanning, push protection, private vulnerability reporting, and default CodeQL are enabled. Protected-path drill was exercised through PR #9: direct pushes to `master` were blocked, required hosted checks caught static-security and backend-gate issues, and final hosted checks passed after fixes.
- Restore-test readiness is documented in `docs/AEVRYN_RESTORE_TEST_PLAN.md`; production backup provider, retention window, restore execution, and audit storage decisions remain open.
- AI provider review is documented in `docs/AEVRYN_AI_PROVIDER_REVIEW.md`; OpenAI remains an internal-alpha candidate only until provider terms, retention, training behavior, disclosure, and release-gate coverage are reviewed.
- Public contact targets are documented in `docs/AEVRYN_PUBLIC_CONTACTS.md`; `support@aevryn.ai`, `privacy@aevryn.ai`, `security@aevryn.ai`, and `abuse@aevryn.ai` are provisioned and tested for inbound routing and outbound SMTP sending.
- Public trust website copy is drafted in `docs/AEVRYN_PUBLIC_TRUST_PAGE_COPY.md`; publication remains blocked by contact provisioning, legal review, backup retention selection, provider review, security operations, and final public-beta signoff.
- Release-candidate run record template is documented in `docs/AEVRYN_RELEASE_CANDIDATE_RUN_RECORD.md`; the actual release-candidate run has not been executed.
- Public beta external setup is consolidated in `docs/AEVRYN_PUBLIC_BETA_SETUP_CHECKLIST.md`; it tracks contact aliases, branch protection, provider review, backup/restore/audit, production-like smoke, public trust/legal publication, and final signoff.
- Public contact alias provisioning is recorded in `docs/AEVRYN_ALIAS_PROVISIONING_RECORD.md`; Cloudflare Email Routing rules exist for support/privacy/security/abuse to `aetherra.project@gmail.com`, inbound delivery from `zyonic88@gmail.com` passed for all four aliases, Gmail filters route them into their respective folders, Cloudflare/Gmail MFA are enabled, and Cloudflare inbound DNS/routing health passed with 9 received, 9 forwarded, 0 failed, and 0 rejected. Cloudflare Email Sending SMTP successfully sent synthetic outbound tests from support/privacy/security/abuse aliases to `zyonic88@gmail.com`, and SPF/DKIM/DMARC received-message verification passed in Gmail. Replies should come from the specific product identity unless Aetherra Labs is intentionally speaking as the company.

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
- Failed import runs now render stable no-snapshot and run-error labels after refresh
- Web Import is visible as an unavailable, permission-check-gated placeholder; no URL fetching is enabled
- Deferred PDF, MOBI, and AZW3 formats are all covered by UI preflight tests that block inspection before the API import endpoint is called

Phase 8 accepted:

- Monitoring is metadata-only observability, not Phase 9 performance optimization
- `docs/AEVRYN_MONITORING.md` defines the first monitoring contract and privacy boundary
- Project status starts with authenticated metadata for latest import, latest engine run, worker/job state, snapshot/export availability, latest failure summary, and recent workflow events
- Frontend API client now consumes the project status contract directly; monitoring UI must display API-provided status rather than infer workflow state
- Project workspace now has a restrained Monitoring tab for API health, current project run state, latest failure, snapshot/export availability, and recent workflow events
- Monitoring tab coverage now proves status API failures surface backend-provided errors without inventing workflow state
- Preview and extraction workflows now emit metadata-only API logs for success/failure with stable workflow kinds and error codes, without source prose or raw AI payloads
- API health now reports metadata-only project/import storage adapter availability, and Monitoring displays those API-provided storage states
- Phase 8 exit verification passed before closeout: backend and frontend gates were green before the final closeout docs pass

Phase 9 accepted:

- Performance architecture is defined in `docs/AEVRYN_PERFORMANCE.md`
- Phase 9 acceptance is governed by `docs/AEVRYN_V2_PHASE_9_ACCEPTANCE.md`
- Phase 9 optimizes latency for the single-user V2 product path; throughput and scalability belong later
- Initial budgets, deterministic timing helpers, metadata-only performance snapshots, baseline JSON artifacts, and regression comparison helpers live in `src/aevryn/performance.py`
- Local V2 baseline generation lives in `src/aevryn/performance_runner.py` and is exposed by `aevryn performance-baseline`
- Baseline comparison is exposed by `aevryn performance-baseline --compare-to <baseline.json>` and exits nonzero only for critical regressions
- Generated local performance baselines belong under ignored `performance-baselines/`
- Baseline measurements cover import inspect, import save, worker processing, snapshot creation, project status, workspace load, export preview, and validation suite
- Frontend workspace-load hardening reuses fresh dashboard health metadata during dashboard-to-monitoring navigation while preserving API-provided monitoring status
- Phase 9 exit verification passed: backend gates, frontend gates, and the local `performance-baseline` command were green before closeout

Phase 10 starting point:

- Phase 10 acceptance is governed by `docs/AEVRYN_V2_PHASE_10_ACCEPTANCE.md`
- Internal alpha readiness is defined in `docs/AEVRYN_INTERNAL_ALPHA.md`
- Repeatable private alpha readiness runs are recorded with `docs/AEVRYN_INTERNAL_ALPHA_CHECKLIST.md`
- Treat Phase 10 as private internal alpha readiness, not public launch
- Verify the complete creator path: register, create project, upload story, wait for processing, view engine outputs, and export
- Treat recovery as distinct from failure display: after browser refresh, session expiry, worker interruption, failed runs, or network/API interruption, answer whether the user can continue
- Version readiness through Smoke Test, Integration Test, Operational Readiness Test, and Release Candidate Test gates
- Preserve all Phase 6-9 boundaries: durable storage, import workflow, monitoring observability, metadata-only performance measurement, and no frontend inference of backend workflow state
- Do not add payments, public launch flows, broad redesign, image generation, video generation, or chatbot behavior in Phase 10 unless explicitly scoped later

Phase 10 progress:

- Internal alpha docs and readiness checklist exist.
- Automated gates are green after alpha hardening through commit `a064bef`.
- Import, processing, monitoring, refresh recovery, project deletion, and retry after extraction failures have been manually exercised through the browser.
- Characters, World, Timeline, Scenes, Continuity, Prompt Packs, and Exports now render processed project output from persisted backend snapshots instead of requiring testers to use developer preview inputs.
- Alpha extraction now dedupes duplicate relationship candidates and presentation hides conflicting gender values instead of showing both.
- Browser sanity testing validated Continuity, Prompt Packs, and Exports against persisted backend snapshots.
- Browser sanity testing found and fixed the local/demo prompt-pack fallback so scene and prompt panels stay available even when extraction accepts no canon facts.
- Private tester instructions are documented in `docs/AEVRYN_PRIVATE_ALPHA_TESTER_GUIDE.md`.
- Phase 10 is ready for narrow private alpha testing with documented limitations; Phase 11 Security & Privacy Hardening is accepted, and public beta now depends on deployment-specific security follow-through.

Phase 11 accepted security/privacy baseline:

- V2 closeout decision is recorded in `docs/AEVRYN_V2_CLOSEOUT.md`
- Phase 11 acceptance is governed by `docs/AEVRYN_V2_PHASE_11_ACCEPTANCE.md`
- Security architecture is documented in `docs/AEVRYN_SECURITY.md`
- Privacy architecture is documented in `docs/AEVRYN_PRIVACY.md`
- API security hardening is documented in `docs/AEVRYN_API_SECURITY_HARDENING.md`
- Audit ledger architecture is documented in `docs/AEVRYN_AUDIT_LEDGER.md`
- Repository secret scanning is documented in `docs/AEVRYN_REPOSITORY_SECRET_SCAN.md`
- Dependency auditing is documented in `docs/AEVRYN_DEPENDENCY_AUDIT.md`
- Static security scanning is documented in `docs/AEVRYN_STATIC_SECURITY_SCAN.md`
- Backup retention boundaries are documented in `docs/AEVRYN_BACKUP_RETENTION.md`
- User-facing trust principles are documented in `docs/AEVRYN_TRUST_MODEL.md` and `docs/AEVRYN_USER_RIGHTS.md`
- Content classification is documented in `docs/AEVRYN_CONTENT_CLASSIFICATION.md`
- Public-launch legal drafts are in `docs/TERMS_OF_SERVICE.md`, `docs/PRIVACY_POLICY.md`, `docs/ACCEPTABLE_USE_POLICY.md`, and `docs/SECURITY_DISCLOSURE.md`
- Data retention and recovery policy drafts are in `docs/DATA_RETENTION_POLICY.md` and `docs/BACKUP_AND_RECOVERY.md`
- Repeatable Phase 11 gates are tracked in `docs/AEVRYN_PHASE_11_SECURITY_GATES.md`
- Phase 11 gates currently list no remaining implementation gates
- Treat Phase 11 as the accepted trust baseline before public beta, not as a product expansion phase
- Opening slice: explicit authorization-boundary verification across project, story, import, run, snapshot, export/status, settings, output, and deletion access
- Core principle: security is architecture, not a feature
- Core privacy principle: uploaded stories, generated canon, and generated exports belong to the creator
- Aetherra Labs must not train on user stories without explicit opt-in
- Deleted stories must be removed from Aevryn-owned active metadata/source storage, and deletion must not create hidden copies in logs, monitoring, audit records, or diagnostics
- Audit ledger work should be metadata-only, tamper-evident, and free of source prose/full AI payloads
- Do not add public launch, payments, collaboration, publishing, media generation, chatbot behavior, or broad redesign as retroactive Phase 11 work

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
