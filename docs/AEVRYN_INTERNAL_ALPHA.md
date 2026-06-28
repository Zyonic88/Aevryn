# Aevryn Internal Alpha

> Built by **Aetherra Labs**

Phase 10 prepares Aevryn V2 for private internal alpha.

Core rule:

```text
Use it.
Break it.
Fix it.
Do not launch it publicly.
```

Internal alpha is not a marketing launch, billing launch, media-generation launch, or broad redesign phase.

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

Phase 10 proves that path is usable enough for trusted private testing.

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

---

# Manual Alpha Checks

Manual alpha checks should cover the parts automation cannot fully judge yet:

* whether the creator path feels understandable without CLI knowledge
* whether loading, empty, and failure states explain what happened
* whether Monitoring helps a tester recover when a workflow fails
* whether output views are useful enough for private testing
* whether export previews produce a file shape a creator recognizes
* whether known limitations are visible before they become confusing

Manual checks must not expand Phase 10 into branding polish, public launch readiness, or media-generation scope.

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
