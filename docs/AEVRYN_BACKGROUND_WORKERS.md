# Aevryn Background Workers

> Built by **Aetherra Labs**

This document defines the Version 2 Phase 3 Background Workers boundary.

---

# Purpose

Background Workers run long platform workflows outside the browser request cycle.

Aevryn must never require the website to wait while imports, extraction, canon updating, presentation, or export workflows execute synchronously.

The Phase 3 worker foundation exists to prove the platform job lifecycle before production queue infrastructure is introduced.

---

# What Is It?

The Background Workers system is the platform execution layer for queued jobs.

It provides:

* Job submission
* Queue records
* Job claiming
* Worker execution
* Deterministic worker drain summaries
* Engine run lifecycle updates
* Failure summaries
* Queue status snapshots
* Job reference validation
* Deterministic local queue behavior

---

# Why Does It Exist?

Creators will upload large chapters, full novels, EPUB files, and future project data.

Those workflows can take time.

The platform needs a safe pattern:

```text
Upload
-> API
-> Queue
-> Worker
-> Engine
-> Project Database
-> Finished
```

This keeps the website responsive and makes failures inspectable.

---

# Authority Owned

The Background Workers system owns:

* Job lifecycle
* Queue submission
* Queue claiming
* Worker execution orchestration
* Retry intent metadata
* Worker failure summaries
* Queue status observability
* Synchronizing job status with engine run status

---

# Authority Not Owned

The Background Workers system does not own:

* Canon truth
* Entity extraction rules
* Story Import parsing rules
* Timeline validity
* Character card logic
* Scene analysis
* Prompt generation
* Presentation view models
* Export serialization
* User authentication
* Project ownership policy
* Production database migrations

---

# Core Rule

Workers execute.

They do not decide truth.

If a worker needs continuity behavior, it must call the Aevryn Engine through established system boundaries.

---

# Phase 3 Implementation

Phase 3 starts with a deterministic local worker foundation:

* `BackgroundJob`
* `InMemoryJobQueue`
* `BackgroundJobService`
* `BackgroundWorker`
* `BackgroundWorkerRunSummary`

This foundation proves the contract without requiring Redis, Celery, RQ, Dramatiq, or a production database adapter yet.

Production queue infrastructure can replace the queue adapter later without changing engine authority.

## Hosted Alpha Auto-Process Bridge

The hosted alpha may enable:

```text
AEVRYN_WORKER_AUTO_PROCESS_SUBMISSIONS=true
```

When enabled, the API records a pending run, enqueues a worker job, starts one
server-side worker drain, and returns the submitted run response without waiting
for provider-backed extraction to finish. The browser never calls the worker
drain endpoint and never receives worker credentials.

This is an alpha bridge for the current process-local queue. It is not the final
production worker posture.

Before public beta, replace this bridge with a persistent managed queue runner
that survives API instance restarts and does not depend on process-local memory.

---

# Job Lifecycle

```text
queued
-> running
-> succeeded
```

or:

```text
queued
-> running
-> failed
```

Jobs cannot move backward.

Completed jobs cannot be claimed again.

Failed jobs require an error summary.

---

# Engine Run Synchronization

Every queued import-processing job creates a pending `engine_runs` record.

When a worker claims the job:

```text
engine_run.status = running
```

When the handler succeeds:

```text
engine_run.status = succeeded
```

When the handler fails:

```text
engine_run.status = failed
engine_run.error_summary = worker failure summary
```

The worker may update run status, but it may not change project, story, or import scope. The claimed queue job must also match the persisted `engine_runs.job_ref`. Missing or mismatched job references fail before handler execution.

---

# Determinism Rule

Given the same queued jobs, the deterministic local queue must claim jobs in the same order and produce the same lifecycle states.

Production queue adapters may have distributed behavior, but their visible job contract must remain stable.

---

# Failure Modes

Background Workers can fail if:

* A duplicate job is submitted
* A job is missing
* A queue adapter fails during enqueue
* A lifecycle transition is invalid
* A handler raises an error
* A repository update fails
* A job references an invalid engine run
* A job does not match the engine run job reference
* Worker timestamps are impossible or malformed
* A worker crashes while running

Failures must be explicit.

Silent success is not allowed.

---

# V2 Phase 3 Rule

Phase 3 builds background execution foundations only.

Do not build:

* Website UI
* User accounts
* Cloud collaboration
* Payments
* Image generation
* Video generation
* Production media pipelines

---

# Acceptance Standard

The Background Workers system is Phase 3 ready when:

* Jobs can be submitted deterministically
* Jobs can be claimed deterministically
* Engine runs are created as pending
* Claimed runs become running
* Successful jobs mark runs succeeded
* Failed jobs mark runs failed with summaries
* Invalid status transitions are rejected
* Queue failures are typed and explicit
* Queue snapshots report deterministic status counts
* Job references are validated before handler execution
* Worker timestamp order is validated before queue mutation
* Worker lifecycle updates survive local JSON repository reloads
* Worker drain loops report claimed, succeeded, and failed jobs
* Failed submissions do not enqueue orphaned jobs
* Queue adapter failures mark pending engine runs failed
* Unit tests pass
* Type checks pass
* Lint checks pass
