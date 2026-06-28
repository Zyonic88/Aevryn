# Aevryn Performance

> Built by **Aetherra Labs**

Phase 9 makes the V2 product path measurably fast enough for internal alpha.

Core rule:

```text
Performance work must be measured, metadata-only, and correctness-preserving.
```

Performance work must not weaken evidence, canon, timeline, export, validation, authentication, storage, monitoring, or frontend authority boundaries.

---

# Scope

Phase 9 optimizes latency for the single-user V2 product path.

Phase 9 does not own:

* multi-user throughput
* horizontal scaling
* distributed workers
* cloud autoscaling
* production database tuning
* cache infrastructure
* broad frontend redesign

Throughput and scalability belong after the V2 product path is stable enough for internal alpha.

---

# Latency Budgets

Performance budgets define what acceptable means.

Initial Phase 9 budgets:

| Area | Target | Warning | Critical |
| --- | ---: | ---: | ---: |
| Import inspect | `<250ms` | `>=500ms` | `>=1s` |
| Project status | `<100ms` | `>=250ms` | `>=500ms` |
| Workspace load | `<1s` | `>=2s` | `>=4s` |
| Export preview | `<500ms` | `>=1s` | `>=2s` |
| Validation suite | measured baseline | large regression | major regression |
| Worker processing | measured only | no fixed warning | no fixed critical |

Worker processing remains measured-only in Phase 9 because runtime depends on story size, source format, parser behavior, and later AI/extraction cost.

---

# Measurement Surface

Phase 9 should measure:

* import inspect latency
* import save latency
* worker job lifecycle duration
* snapshot creation duration
* project status latency
* export preview latency
* frontend workspace load behavior
* validation suite duration
* memory-sensitive paths where practical

The local `workspace_load` baseline measures the read-only project workspace metadata path: project shell metadata plus the backend-provided project status summary. Browser rendering and visual polish remain outside this backend baseline.

Measurements are metadata.

They may include:

* stable benchmark names
* elapsed milliseconds
* budget status
* workflow kind
* stable machine error code
* run, import, snapshot, or export IDs where already allowed by monitoring policy

They must not include:

* source prose
* full AI responses
* generated export content
* credentials
* session tokens
* machine-local paths
* volatile timestamps inside deterministic outputs

---

# Regression Snapshots

Phase 9 may store a metadata-only performance snapshot for intentional baseline comparisons.

A performance snapshot may record:

* schema version
* stable benchmark names
* elapsed milliseconds
* budget status

It must not record:

* source text
* generated outputs
* machine paths
* timestamps
* hostnames
* usernames

Regression checks should tolerate small variance and flag large changes.

The goal is not to fail because `145ms` became `148ms`.

The goal is to catch regressions like `145ms` becoming `920ms`.

The initial performance helper is `src/aevryn/performance.py`. It owns budget classification, metadata-only snapshot construction, deterministic operation timing, and snapshot-to-snapshot regression comparison.

Local measured baseline files should be written under `performance-baselines/`, which is ignored by default. Committing a measured baseline should be an intentional release decision, not a side effect of running benchmarks on one machine.

Generate a local in-memory V2 baseline with:

```powershell
aevryn performance-baseline
```

Compare a previous baseline against a new local run with:

```powershell
aevryn performance-baseline --compare-to performance-baselines/previous.json
```

The comparison tolerates small variance, reports warning and critical regressions, and exits nonzero only for critical regressions.

The baseline JSON artifact envelope is:

```text
artifact_kind: aevryn_phase9_performance_baseline
schema_version: 1
snapshot: metadata-only performance snapshot
```

---

# Optimization Rule

Phase 9 must measure before optimizing.

Each optimization should identify:

* measured bottleneck
* change made
* before/after result or reason no change was worthwhile
* correctness checks that still pass

If further optimization gives marginal returns or pushes into throughput/scalability, stop and leave it for a later phase.

---

# Optimization Log

Initial Phase 9 frontend hardening reduced redundant metadata requests during workspace navigation. Dashboard API health data now remains fresh for a short window and is reused by the Monitoring view instead of being refetched immediately during dashboard-to-workspace navigation.

Measured bottleneck:

* frontend workspace load behavior: repeated metadata queries during quick navigation between dashboard and monitoring surfaces

Change made:

* shared frontend query policy disables focus-triggered refetches and keeps successful metadata queries fresh for 10 seconds
* regression coverage verifies dashboard-to-monitoring navigation performs one API health request while still rendering backend-provided monitoring status

Correctness checks:

* backend gates: `pytest -q`
* frontend gates: `npm.cmd test -- --run --reporter=dot`, `npm.cmd run lint`, `npx.cmd tsc -p tsconfig.json --noEmit`, `npm.cmd run build`
