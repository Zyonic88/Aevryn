# Aevryn V2 Phase 9 Acceptance

> Built by **Aetherra Labs**

Phase 9 makes Aevryn measurably fast enough for internal alpha.

Core rule:

```text
Measure.
Budget.
Detect regressions.
Optimize only where measured.
```

Phase 9 must not become a throughput, production infrastructure, cloud scaling, or frontend redesign phase.

---

# Required Contract

Phase 9 starts with:

* `docs/AEVRYN_PERFORMANCE.md`
* typed performance budgets
* metadata-only performance snapshots
* stable metadata-only baseline JSON artifacts
* deterministic operation timing helpers
* a local CLI command for generating ignored baseline artifacts
* a local CLI comparison mode for warning and critical regressions
* regression checks that tolerate normal variance but catch large slowdowns

Performance metadata must stay outside deterministic canon, evidence, export, and validation outputs.

---

# Acceptance Criteria

Phase 9 is accepted.

Accepted criteria:

* Performance architecture is documented.
* Latency budgets exist for import inspect, project status, workspace load, and export preview.
* Worker processing is measured without a fixed SLA.
* Latency and throughput are explicitly separated.
* Baseline measurements exist for import, worker, snapshot, export, project status, frontend workspace load, and validation.
* Performance snapshots are metadata-only.
* Generated local baseline files are ignored by default.
* Operation timing returns elapsed metadata without serializing source or generated payloads.
* Performance snapshots do not include source prose, AI payloads, generated exports, machine-local paths, credentials, tokens, hostnames, usernames, or timestamps.
* Regression checks tolerate small variance and flag major slowdowns.
* Deterministic validation output remains byte-stable.
* No canon, evidence, timeline, export, validation, storage, authentication, monitoring, or frontend authority boundary is weakened.
* At least one measured bottleneck is improved or explicitly documented as not worth changing.
* Backend gates pass.
* Frontend gates pass.

Accepted implementation:

* `docs/AEVRYN_PERFORMANCE.md` defines the performance architecture, latency budgets, throughput boundary, metadata-only snapshot policy, and optimization log.
* `src/aevryn/performance.py` owns typed budgets, deterministic operation timing, metadata-only baseline JSON artifacts, and warning/critical regression comparison.
* `aevryn performance-baseline` generates ignored local baseline artifacts with measurements for import inspect, import save, worker processing, snapshot creation, project status, workspace load, export preview, and validation suite.
* `aevryn performance-baseline --compare-to <baseline.json>` reports warning and critical regressions and exits nonzero only for critical regressions.
* Frontend workspace-load hardening reuses fresh dashboard health metadata during dashboard-to-monitoring navigation while still rendering API-provided monitoring status.

---

# Out Of Scope

Phase 9 does not include:

* multi-user throughput optimization
* distributed worker scaling
* cloud autoscaling
* production database tuning
* cache infrastructure
* new admin consoles
* broad frontend redesign
