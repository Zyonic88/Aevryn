# Aevryn Release Candidate Test Readiness

> Built by **Aetherra Labs**

This document tracks V2 Release Candidate Readiness Gate 8.

Gate 8 defines the repeatable release-candidate test pass required before public beta approval.

---

# Status

```text
Gate: Release Candidate Test Pass
Status: Not started
Public beta: Blocked
```

Private alpha readiness is recorded in `docs/AEVRYN_INTERNAL_ALPHA_CHECKLIST.md`.

Public beta requires a broader release-candidate pass after production-readiness decisions are made.

---

# Core Rule

```text
Public beta must be repeatable, not lucky.
```

Aevryn should be able to rerun the release-candidate gate and get the same confidence before inviting untrusted users to upload manuscripts.

---

# Required Automated Gates

The release-candidate test pass must include:

* backend tests
* frontend tests
* backend lint
* frontend lint
* backend typing
* frontend type checking
* frontend production build
* dependency audits
* repository secret scan
* static security scan
* performance regression check
* release-readiness document tests

Every command should be documented with expected results.

Failures must block release unless a residual risk is explicitly documented and accepted.

---

# Required Product Smoke

The release-candidate smoke path must verify:

* register or log in
* create project
* create or select story
* upload supported files
* inspect import
* save import
* submit processing
* observe run state
* process queued work
* observe snapshot availability
* review Characters
* review World
* review Timeline
* review Scenes
* review Continuity
* review Prompt Packs
* review Exports
* create export preview
* delete project

The smoke path must not require CLI knowledge from a tester.

---

# Required Recovery Checks

The release-candidate pass must verify:

* browser refresh recovery
* login/session recovery
* API outage messaging
* failed-run visibility
* retry after failed run
* stale worker/job handling
* import retry after failure
* project deletion completion
* monitoring state accuracy
* no frontend-inferred workflow state

Users should be able to answer:

```text
Can I continue?
```

after common failure paths.

---

# Required Privacy Checks

The release-candidate pass must verify that no test output exposes:

* full manuscripts
* full chapters
* full AI responses
* full export content unless explicitly previewed
* credentials
* tokens
* private URLs
* hostnames
* usernames
* machine-local paths

Diagnostics, monitoring, logs, errors, support guidance, and audit records must remain metadata-only.

---

# Required Production-Like Smoke

Before public beta, Aevryn needs a production-like deployment smoke test that proves:

* production configuration fails closed when required settings are missing
* configured browser origins are explicit
* HTTPS behavior is defined at the edge
* workflow routes are protected
* storage references resolve inside project ownership boundaries
* `aevryn production-config-check` passes without printing secrets
* worker processing can complete
* monitoring observes workflow state
* export preview works
* logs remain metadata-only

This does not require public launch, but it must run outside the purely local private-alpha path.

---

# Manual Alpha-To-Beta Pass

The final manual pass should record:

* tester
* date
* commit
* environment
* imported chapter count
* provider mode
* pass/fail result
* known limitations
* accepted residual risks
* whether public beta is approved or blocked

Manual findings must be resolved or explicitly accepted before public beta.

---

# Signoff

Release-candidate signoff must include:

* product signoff
* security signoff
* privacy signoff
* legal signoff
* operations signoff
* support signoff

If one role is held by the same person during early Aetherra Labs work, the signoff record must still name the responsibility being accepted.

---

# Public Beta Blockers

Public beta remains blocked until:

* backend gates pass
* frontend gates pass
* dependency audits pass
* secret scan passes
* static security scan passes
* performance regression check passes
* private alpha smoke path passes
* production-like deployment smoke test passes
* final manual alpha-to-beta pass is recorded
* release-candidate signoff is recorded

---

# Acceptance

Gate 8 is accepted when:

```text
Release candidate behavior is repeatable, documented, privacy-preserving, and signed off before public beta.
```
