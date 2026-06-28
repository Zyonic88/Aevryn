# Aevryn Monitoring

> Built by **Aetherra Labs**

Phase 8 makes platform workflows observable without changing engine behavior.

Monitoring answers:

* What happened?
* Which project, story, import, run, or snapshot was involved?
* Did the workflow succeed, fail, or remain pending?
* What stable error summary can the UI or operator show next?

It does not optimize runtime performance. That belongs to Phase 9.

---

# Scope

Phase 8 monitors metadata for:

* imports
* engine runs
* background workers
* snapshots
* preview workflows
* export workflows
* API health and storage availability

Monitoring must stay metadata-only.

It must not log or expose:

* full source chapters
* full AI responses
* full generated exports
* private story prose
* credentials or session tokens

---

# First Contract

The first Phase 8 contract is project status:

```text
GET /v2/projects/{project_id}/status
```

The route reports durable workflow metadata inside the authenticated project boundary:

* project status
* latest import
* latest engine run
* worker/job state
* snapshot availability
* export availability
* latest failure summary
* recent workflow events

The route does not execute workers, inspect source, generate snapshots, or return source text.

---

# Logging Boundary

Phase 8 extends `docs/AEVRYN_LOGGING_POLICY.md`.

Structured monitoring data may identify:

* project IDs
* story IDs
* import IDs
* run IDs
* snapshot IDs
* preview workflow kinds
* extraction workflow kinds
* status values
* stable error summaries

It must not include the source payload or generated prose that caused the status.

Preview and extraction workflows emit metadata-only API logs for success and failure. These logs may include source IDs, safe filenames, source formats, scene IDs, scene counts, workflow kinds, status values, and stable error codes. They must not include full chapter text or raw AI responses.

---

# Acceptance Standard

Phase 8 is ready when:

* meaningful import, run, worker, snapshot, preview, and export workflows are observable
* failures have stable codes or summaries suitable for UI display
* project status can explain durable workflow state after refresh
* monitoring responses remain authenticated and ownership-scoped
* monitoring tests prove source prose is not exposed
* frontend monitoring uses API data and does not bypass the API client
