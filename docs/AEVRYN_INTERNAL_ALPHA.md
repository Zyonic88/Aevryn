# Aevryn Internal Alpha

> Built by **Aetherra Labs**

Phase 10 prepares Aevryn V2 for internal alpha.

Core rule:

```text
Use it.
Break it.
Fix it.
Do not launch it publicly.
```

Internal alpha is not a marketing launch, billing launch, media-generation launch, broad redesign phase, private tester program, or public beta.

---

# Audience Boundary

Internal alpha is limited to Aetherra Labs owner/operator development and Codex-assisted verification.

It is not an invite-only tester program.

It is not a public preview.

It is not approval to accept outside manuscripts.

Public beta is the first milestone where outside users may be invited to upload their own work, and it remains blocked until the public-beta gates are signed off.

---

# Goal

A creator should be able to complete the V2 product path without touching the CLI:

```text
Register
-> Create Project
-> Upload Story
-> Wait For Processing
-> View Character Cards
-> View World
-> View Timeline
-> View Scene Sheets
-> View Prompt Packs
-> Export
```

Phase 10 proves that path is usable enough for continued internal development and release-candidate hardening.

---

# Alpha Readiness Surface

Phase 10 owns readiness across the existing product path:

* authentication and session persistence
* project creation and project return
* story metadata
* supported-format import
* saved import metadata
* queued run submission
* worker processing
* snapshot availability
* monitoring status
* engine output views
* export preview
* performance baseline generation
* clear user-facing failures
* recovery after interrupted workflows

Phase 10 must preserve the authority boundaries from earlier phases:

* backend owns workflow state
* frontend displays API-provided workflow state
* monitoring observes workflows and does not execute them
* performance metadata stays outside canon, evidence, exports, and validation output
* no source prose, full AI response, full generated export, credential, or token is logged in diagnostics

---

# Alpha Smoke Path

The alpha smoke path should exercise:

* register or log in
* create a project
* create or select a story
* inspect a supported source file or pasted source
* save the import
* submit a run
* process the queued run
* observe status in Monitoring
* confirm canon snapshot availability
* open each engine output view
* create an export preview
* generate a local performance baseline

The smoke path should be automated where practical and documented where manual verification is still required.

---

# Recovery

Recovery is different from failure handling.

Failure answers:

```text
What broke?
```

Recovery answers:

```text
Can the user continue?
```

Phase 10 recovery checks should cover:

* browser refresh restores the project workspace from API-backed state
* saved imports, runs, snapshots, and exports remain visible after refresh
* session expiry returns the user to login without corrupting workspace state
* login after session expiry returns the user to a useful project state where practical
* worker interruption or restart does not corrupt project state
* queued, running, succeeded, and failed worker states remain observable
* failed runs can be understood from Monitoring without source-prose leakage
* network or API interruption does not cause the frontend to invent workflow state
* reconnecting preserves API-owned project truth

Recovery checks may be automated or manual depending on the interruption being tested, but every recovery result should say whether the user can continue.

---

# Readiness Test Ladder

Phase 10 readiness should be versioned and repeatable.

Record readiness runs in `docs/AEVRYN_INTERNAL_ALPHA_CHECKLIST.md`.

Use this ladder:

* Smoke Test: fast confidence that the happy path works.
* Integration Test: real subsystems cooperate across auth, storage, imports, workers, snapshots, monitoring, exports, and performance baselines.
* Operational Readiness Test: interruption, recovery, observability, diagnostics, and safe failure behavior.
* Release Candidate Test: full repeatable pre-alpha gate before public-beta readiness work.

Each ladder step should have a stable name, scope, owner, date, result, and known limitations. A failed higher-level test should not erase lower-level evidence; it should identify the next fix.

---

# Automated Gates

Automated alpha gates should include:

* backend tests
* frontend tests
* backend lint and type checks
* frontend lint, type checks, and production build
* Aevryn validation
* local performance baseline generation
* backend alpha smoke path
* frontend alpha route smoke where practical
* automated recovery checks where practical

---

# Manual Alpha Checks

Manual alpha checks should cover the parts automation cannot fully judge yet:

* whether the creator path feels understandable without CLI knowledge
* whether loading, empty, and failure states explain what happened
* whether Monitoring helps the internal operator recover when a workflow fails
* whether output views are useful enough for internal alpha hardening
* whether export previews produce a file shape a creator recognizes
* whether known limitations are visible before they become confusing
* whether interrupted workflows let the internal operator continue

Manual checks must not expand Phase 10 into branding polish, public launch readiness, or media-generation scope.

The former private tester guide is retained as an internal alpha operator guide in `docs/AEVRYN_PRIVATE_ALPHA_TESTER_GUIDE.md`.

---

# Known Non-Goals

Phase 10 does not include:

* public launch
* payments
* subscriptions
* teams
* collaboration
* publishing
* image generation
* video generation
* chatbot behavior
* production cloud deployment
* broad visual redesign
* new admin console

Those belong to later phases unless explicitly rescoped.
