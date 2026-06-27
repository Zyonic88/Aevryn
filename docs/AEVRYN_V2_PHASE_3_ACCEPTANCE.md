# Aevryn V2 Phase 3 Acceptance Criteria

> Built by **Aetherra Labs**

This document defines when Version 2 Phase 3, Background Workers, can be considered complete.

---

# Goal

Create a reliable background execution foundation so platform workflows do not run inside browser request cycles.

Phase 3 proves job submission, queue lifecycle, worker execution, and engine run status synchronization.

---

# Required Capabilities

## Job Model

* Jobs have permanent IDs
* Jobs have a known kind
* Jobs reference project, story, import, and engine run scope
* Jobs track status
* Jobs track queued and status-update timestamps
* Failed jobs require error summaries
* Job records validate invalid lifecycle states

## Queue

* Jobs can be enqueued
* Duplicate jobs are rejected
* Queued jobs can be claimed
* Claimed jobs become running
* Running jobs can succeed
* Running jobs can fail
* Non-running jobs cannot be completed
* Queue reads are deterministic
* Queue status snapshots are deterministic

## Worker

* Workers claim one job at a time
* Idle workers return no work
* Workers call a handler instead of owning business logic
* Workers can drain available jobs with an explicit limit
* Worker drain loops return deterministic summaries
* Handler success marks the queue job succeeded
* Handler failure marks the queue job failed
* Handler failure records a concise error summary

## Project Database Interaction

* Job submission creates a pending engine run
* Queue enqueue failures mark pending engine runs failed
* Worker claim marks the engine run running
* Worker success marks the engine run succeeded
* Worker failure marks the engine run failed
* Worker updates cannot change run project, story, or import scope
* Claimed jobs must match persisted engine run job references
* Missing job references fail before handler execution
* Worker run reads use a trusted worker repository boundary
* Worker status updates persist through durable local repositories

## Boundaries

* Workers do not own canon truth
* Workers do not own extraction rules
* Workers do not own presentation view models
* Workers do not own export serialization
* Workers do not own authentication
* Workers do not bypass the engine

---

# Tests Required

* Unit tests for job validation
* Unit tests for queue ordering
* Unit tests for invalid queue transitions
* Unit tests for duplicate and missing jobs
* Unit tests for successful worker execution
* Unit tests for failed worker execution
* Unit tests for queue status snapshots
* Unit tests for job reference mismatch protection
* Unit tests for missing job references
* Unit tests for impossible worker timestamp ordering
* Integration tests for JSON repository worker status reloads
* Regression tests preventing orphaned queued jobs
* Regression tests for queue enqueue failure cleanup
* Unit tests for worker drain loops and summaries
* Tests proving engine run status synchronization
* Tests proving run scope is preserved

---

# Phase 3 Complete Means

Phase 3 is complete when:

* `ruff` passes
* `mypy` passes
* `pytest` passes
* Background worker docs are complete
* Worker interfaces are stable enough for Phase 4 and later API integration
* Remaining improvements are production adapter choices rather than core architecture gaps

---

# Not Phase 3

The following belong to later phases or deployment choices:

* Redis adapter
* Celery, RQ, or Dramatiq deployment
* User authentication
* Website UI
* Payment workflows
* Image generation
* Video generation
* Cloud collaboration
