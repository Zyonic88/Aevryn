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

Phase 9 is accepted when:

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
