# Aevryn V2 Phase 10 Acceptance

> Built by **Aetherra Labs**

Phase 10 makes Aevryn ready for internal alpha.

Core rule:

```text
Internal alpha readiness.
Not public launch.
```

Phase 10 must prove the V2 creator path can be used without the CLI, while keeping all earlier evidence, storage, monitoring, performance, authentication, and frontend authority boundaries intact.

---

# Required Contract

Phase 10 starts with:

* `docs/AEVRYN_INTERNAL_ALPHA.md`
* `docs/AEVRYN_INTERNAL_ALPHA_CHECKLIST.md`
* `docs/AEVRYN_PRIVATE_ALPHA_TESTER_GUIDE.md`
* this acceptance document
* a complete alpha smoke path
* a clear split between automated gates and manual alpha checks
* a recovery plan for interrupted workflows
* a versioned readiness test ladder
* known limitations documented before public-beta readiness review

---

# Acceptance Criteria

Phase 10 is accepted when:

* Internal alpha architecture is documented.
* The complete creator path is covered by an alpha smoke plan.
* The smoke path covers auth, project creation, story/import workflow, worker processing, monitoring, output views, export preview, and performance baseline generation.
* Recovery is covered as its own readiness layer, separate from failure display.
* Recovery checks explain whether the user can continue after refresh, session expiry, worker interruption, failed runs, or network/API interruption.
* Readiness tests are organized as Smoke Test, Integration Test, Operational Readiness Test, and Release Candidate Test.
* Readiness runs record result, known limitations, and whether the internal operator can continue.
* Backend workflow state remains API-owned.
* Frontend does not infer backend workflow state.
* Monitoring observes workflows and does not execute workflows.
* Performance baselines remain metadata-only.
* No full source prose, AI response, generated export, credential, token, hostname, username, or machine-local path is exposed in alpha diagnostics.
* Known alpha limitations are documented.
* Backend gates pass.
* Frontend gates pass.
* Aevryn validation passes.

---

# Out Of Scope

Phase 10 does not include:

* public launch
* payments or subscriptions
* team workflows
* cloud collaboration
* publishing
* image generation
* video generation
* chatbot behavior
* production cloud deployment
* broad frontend redesign
* new admin console
