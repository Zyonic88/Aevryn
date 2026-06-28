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

The first Phase 8 contract is project workflow status:

```text
GET /v2/projects/{project_id}/workflow-status
```

The route reports durable workflow counters inside the authenticated project boundary:

* story count
* saved import count
* total run count
* pending, running, succeeded, and failed run counts
* snapshot count
* latest run ID
* latest run status
* latest run error summary

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
* status values
* stable error summaries

It must not include the source payload or generated prose that caused the status.

---

# Acceptance Standard

Phase 8 is ready when:

* meaningful import, run, worker, snapshot, preview, and export workflows are observable
* failures have stable codes or summaries suitable for UI display
* project workflow status can explain durable workflow state after refresh
* monitoring responses remain authenticated and ownership-scoped
* monitoring tests prove source prose is not exposed
* frontend monitoring uses API data and does not bypass the API client
