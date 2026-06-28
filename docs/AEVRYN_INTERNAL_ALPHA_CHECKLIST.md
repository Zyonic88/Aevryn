# Aevryn Internal Alpha Checklist

> Built by **Aetherra Labs**

Use this checklist for repeatable Phase 10 readiness runs.

Internal alpha is private. This checklist does not approve public launch, billing, collaboration, media generation, or production cloud deployment.

---

# Readiness Run Record

Readiness Run ID:

Date:

Owner:

Build or Commit:

Environment:

Result:

Known Limitations:

Can the tester continue?

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

Known Limitations:

Can the tester continue?

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

Known Limitations:

Can the tester continue?

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

Known Limitations:

Can the tester continue?

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

Known Limitations:

Can the tester continue?
