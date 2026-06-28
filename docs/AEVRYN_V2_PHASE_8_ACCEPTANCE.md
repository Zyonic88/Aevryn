# Aevryn V2 Phase 8 Acceptance

> Built by **Aetherra Labs**

Phase 8 makes Aevryn observable.

Core rule:

```text
Monitoring observes workflows. It does not execute workflows.
```

Phase 8 must not become an admin console, performance phase, or worker control plane.

---

# Required Contract

The first project monitoring contract is:

```text
GET /v2/projects/{project_id}/status
```

It must answer, using metadata only:

* project status
* latest import
* latest engine run
* worker/job state
* snapshot availability
* export availability
* latest failure summary
* recent workflow events

It must not return:

* full chapter text
* full AI responses
* full generated exports
* credentials
* session tokens

---

# Acceptance Criteria

Phase 8 is accepted when:

* API request IDs are present on success and error responses.
* Workflow errors use stable machine codes.
* Project status explains pending, running, succeeded, and failed workflow state.
* Import, run, worker, snapshot, and export events are observable.
* Failures include concise summaries.
* No full chapter text is logged or returned by monitoring contracts.
* No full AI response is logged or returned by monitoring contracts.
* Frontend displays API-provided status only.
* Frontend does not infer backend workflow state.
* Backend gates pass.
* Frontend gates pass.

---

# Frontend Boundary

The frontend monitoring surface must be restrained.

It may show:

* API health
* current project run state
* latest failure
* snapshot/export availability
* recent workflow events

It must not create a broad admin console in Phase 8.
