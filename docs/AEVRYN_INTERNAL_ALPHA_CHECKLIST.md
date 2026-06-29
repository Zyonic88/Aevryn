# Aevryn Internal Alpha Checklist

> Built by **Aetherra Labs**

Use this checklist for repeatable Phase 10 readiness runs.

Internal alpha is private. This checklist does not approve public launch, billing, collaboration, media generation, or production cloud deployment.

---

# Readiness Run Record

Readiness Run ID:

phase10-readiness-2026-06-28-001

Date:

2026-06-28

Owner:

Codex / Aetherra Labs

Build or Commit:

44504dd

Environment:

Local Windows workspace at `C:\Users\enigm\Documents\Aevryn`; validation source root `C:\Users\enigm\Desktop\Aevryn test chapters`.

Result:

Automated readiness gates passed. Manual alpha UX pass found a release-candidate blocker, and follow-up alpha hardening resolved the broad output-surface gap at the contract level. Import, processing, Characters, World, Timeline, Scenes, Continuity, Prompt Packs, and Exports now have API-backed processed project output surfaces. A browser sanity pass is still needed before broad trusted tester invitation.

Known Limitations:

Production database, identity provider, object storage, deployment, public launch, payments, collaboration, media generation, and broad visual redesign remain out of Phase 10 scope. Web Import remains unavailable. Worker interruption is observable through status, but durable retry/reclaim policy belongs to a later production worker phase.

Can the tester continue?

Yes for the tested API-backed workflow, refresh recovery, session recovery, failed-run visibility, worker interruption observability, import retries, and processed output review. Not yet for broad trusted tester invitation until the new Continuity, Prompt Packs, and Exports processed panels receive a browser sanity pass.

---

# Smoke Test

Scope:

Fast confidence that the core creator path works without CLI use.

Required checks:

* Register or log in.
* Create a project.
* Create or select a story.
* Inspect and save a supported import.
* Submit a processing run.
* Process the queued run.
* Open Monitoring.
* Confirm snapshot availability.
* Open Characters, World, Timeline, Scenes, Continuity, Prompt Packs, and Exports.
* Create an export preview.

Result:

PASS. Backend alpha smoke coverage and frontend alpha route smoke coverage exercise the creator path through auth, project creation, import, processing, Monitoring, output views, and export preview.

Known Limitations:

Smoke coverage is automated against deterministic local services and mocked frontend API responses; it is not a hosted-browser exploratory session.

Can the tester continue?

Yes. The happy path is covered without CLI use at the product-contract level.

---

# Integration Test

Scope:

Prove real subsystems cooperate across auth, storage, imports, workers, snapshots, monitoring, exports, and performance baselines.

Required checks:

* Backend gates pass.
* Frontend gates pass.
* Aevryn validation passes.
* Local performance baseline generation passes.
* API request IDs are present on success and error responses.
* No frontend component bypasses the API client.
* No source prose, full AI response, full export content, credential, token, hostname, username, or machine-local path appears in diagnostics.

Result:

PASS. Backend tests, frontend tests, lint, type checks, production build, validation corpus, and local performance baseline generation passed.

Known Limitations:

Performance baseline was generated locally and intentionally left as an ignored machine-local artifact. It is evidence for this readiness run, not a committed release baseline.

Can the tester continue?

Yes. Auth, storage, imports, workers, snapshots, monitoring, exports, and performance baseline generation are cooperating in automated gates.

---

# Operational Readiness Test

Scope:

Prove interrupted workflows are observable and recoverable enough for trusted private testing.

Required checks:

* Browser refresh restores the project workspace from API-backed state.
* Saved imports, runs, snapshots, and exports remain visible after refresh.
* Session expiry returns the user to login without corrupting workspace state.
* Login after session expiry returns to a useful project state where practical.
* Worker interruption is observable through project status, worker state, latest run state, and recent workflow events.
* Queued, running, succeeded, and failed worker states remain observable.
* Failed runs are understandable from Monitoring without source-prose leakage.
* Network or API interruption does not cause the frontend to invent backend workflow state.
* Reconnecting preserves API-owned project truth.

Result:

PASS for automated recovery checks. Manual interruption review remains pending.

Known Limitations:

Automated coverage proves refresh recovery, session-expiry return, failed-run visibility, status API failure handling, and running worker interruption observability. It does not yet prove production worker restart/reclaim semantics because production worker infrastructure is out of Phase 10 scope.

Can the tester continue?

Yes for tested recovery paths. For a claimed running job after interruption, the user can continue by observing the backend-provided running state in Monitoring; automatic reclaim/retry is a later production-readiness concern.

---

# Release Candidate Test

Scope:

Full repeatable pre-alpha gate before inviting trusted testers.

Required checks:

* Smoke Test passed.
* Integration Test passed.
* Operational Readiness Test passed.
* Known limitations are documented before tester invitation.
* Manual alpha checks passed or have explicit accepted limitations.
* No Phase 10 non-goals were added.
* Private tester instructions are clear enough to run without CLI knowledge.

Result:

PARTIAL PASS. Automated gates passed, and manual browser passes proved registration, project creation, story creation, supported multi-file import, import save, run submission, local worker processing, Monitoring, snapshot availability, refresh recovery, project deletion, import retry after failures, and processed-output review for Characters, World, Timeline, and Scenes. Follow-up contract hardening added processed Continuity, Prompt Packs, and Exports panels from persisted backend snapshots. A final browser sanity pass is still needed before trusted tester invitation.

Known Limitations:

Manual browser pass findings:

* Follow-up alpha hardening moved project creation directly into the workspace and replaced shell-facing wording with creator-facing project/workspace language.
* Follow-up alpha hardening reduced visible machine references in import, monitoring, and preview controls while preserving backend identifiers as API data.
* Project and story lists show raw ISO timestamps.
* Import inspection, save, run submission, worker processing, Monitoring, and refresh recovery are usable.
* The initial Project Runs panel showed "Failed to fetch" before a run existed, then recovered after run submission.
* The Source text control is visible but was not reachable through the label API during browser automation.
* Web Import is clearly unavailable, as expected for Phase 10.
* Character Cards, World, Timeline, Scene Sheets, Continuity, Prompt Packs, and Exports now render processed project output from backend snapshots.
* Export output intentionally lists available export kinds and formats; full serialized export content remains behind explicit export preview.
* Alpha AI extraction can still misclassify sparse race/gender evidence when source language is indirect; presentation now hides conflicting gender values instead of showing both.

Can the tester continue?

Yes for continued internal alpha development and narrow operator-led testing of the full output path. Not yet for broad trusted tester invitation until the newly completed output panels pass a browser sanity pass.
