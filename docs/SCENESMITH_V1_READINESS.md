# SceneSmith V1 Readiness

> Built by **Aetherra Labs**

This document tracks whether each Version 1 system is documented, implemented, tested, and usable through the proof workflow.

Acceptance is governed by `docs/SCENESMITH_V1_ACCEPTANCE_CRITERIA.md`.

Functional does not mean complete.

A subsystem is V1 complete only when every required acceptance criterion is checked.

V1 readiness means:

* The system has a clear authority boundary.
* The system has tests for its V1 behavior.
* The system does not own another system's responsibility.
* The system can participate in the continuity pipeline.
* The system avoids V2 features such as media generation, accounts, payments, and cloud collaboration.
* The system satisfies the universal V1 checklist.

---

## Current Status

| System | V1 Status | Notes |
| --- | --- | --- |
| Story Import | Acceptance Hardened, Pending Canon Test | Imports text, parses chapters/scenes, creates paragraph and sentence evidence anchors, repairs common encoding artifacts, supports numbered web-novel headings, logs import summaries. |
| Translation Engine | Foundation Only | Documented boundary. Optional for V1 and not required to prove continuity. |
| Entity Extraction | Acceptance Hardened, Pending Canon Test | Evidence-bounded extraction validates full AI payload shape, rejects unsupported keys, validates confidence range, requires scene anchors, normalizes candidate text, and logs candidate counts. |
| Canon Updating | Acceptance Hardened, Pending Canon Test | Accepts/rejects candidates using confidence, evidence, and known-entity checks; generic non-character entities are stored explicitly; duplicate entity versions and duplicate semantic relationships are idempotent. |
| Canon Engine | Acceptance Hardened, Pending Canon Test | Stores evidence-backed truth, relationships, state changes, and generic entities; rejects conflicting reused permanent IDs, keeps duplicate updates idempotent, and retrieves current facts by timeline order instead of ID order. |
| Timeline Engine | Acceptance Hardened, Pending Canon Test | Tracks chapters, scenes, events, state changes, and story position; rejects overlapping validity windows, keeps duplicate state-change writes idempotent, prevents conflicting ID reuse, and returns deterministic story-order history. |
| Character Engine | Acceptance Hardened, Pending Canon Test | Builds living character cards from Canon and Timeline; rejects non-character and unknown entities, validates explicit story positions, preserves unknowns, uses active display-name facts, and derives previous values from timeline-ordered Canon history. |
| World Engine | Acceptance Hardened, Pending Canon Test | Builds deterministic world-state views from Canon; rejects character entities, validates relationship endpoints, preserves evidence references, uses active display-name facts, and remains a read layer. |
| Scene Engine | Acceptance Hardened, Pending Canon Test | Builds deterministic canon-backed scene context; validates scene positions through Timeline, deduplicates repeated inputs, returns relationships in stable order, and includes related location IDs when relationships prove them. |
| Scene Analyzer | Acceptance Hardened, Pending Canon Test | Produces deterministic scene meaning, mood, purpose, visual highlights, and continuity notes; validates snapshot/scene consistency, avoids unsupported named conflict claims, deduplicates repeated outputs, and separates retained canon from newly introduced changes. |
| Prompt Engine | Acceptance Hardened, Pending Canon Test | Builds deterministic prompt bundles and production packs from scene context and analysis; deduplicates repeated lines, shortens long analysis text, avoids raw chapter dumps, and never calls external AI tools. |
| Presentation Engine | Acceptance Hardened, Pending Canon Test | Builds deterministic human-readable character, scene, world, and production pack views; validates scene/analysis alignment, deduplicates repeated display items, shortens long prompt lines, and remains separate from Export. |
| Export Engine | Acceptance Hardened, Pending Canon Test | Exports machine and presentation outputs to deterministic JSON, Markdown, and CSV; sorts exported facts, relationships, events, and state changes, includes complete scene snapshot identifiers, exports evidence-rich Continuity Reports, deduplicates Markdown lists, and never writes files directly. |
| Project Manager | Acceptance Hardened, Pending Canon Test | Coordinates import, extraction, canon update, character cards, scene context, prompts, world state, and evidence-rich Continuity Reports; rejects empty imported sources, validates single-scene extractor output, validates multi-scene AI candidate envelopes, deduplicates selected IDs, and stays orchestration-only. |
| CLI Proof Workflow | Acceptance Hardened, Pending Canon Test | Supports import, extraction prompt, single-scene and multi-scene AI JSON application, character, scene, prompt, world, and continuity commands; reports expected workflow errors to stderr with exit code 1, deduplicates repeated selected IDs, and keeps orchestration in Project Manager. |
| Web Import | Documented Only | V1 should prefer manual upload/paste until permission and rate-limit handling are implemented. |

---

## Known Cross-System Gaps

These gaps prevent any implemented subsystem from being marked V1 complete yet:

* Logging policy is documented and tested in `docs/SCENESMITH_LOGGING_POLICY.md`.
* Acceptance checklists are now tracked in `docs/SCENESMITH_V1_ACCEPTANCE_AUDIT.json`.
* Continuity Report exists; real Chapter 1 -> Chapter 4 Canon Test has not been run yet.
* Chapter 1 -> Chapter 4 continuity validation has not been run.

---

## Hardening Order

1. Story Import
2. Entity Extraction
3. Canon Updating
4. Canon Engine
5. Timeline Engine
6. Character Engine
7. World Engine
8. Scene Engine
9. Scene Analyzer
10. Prompt Engine
11. Presentation Engine
12. Export Engine
13. Project Manager
14. CLI Proof Workflow

Translation and Web Import remain boundary systems until the core continuity loop requires them.

---

## Canon Test Target

After subsystem acceptance, SceneSmith must run a continuity test across:

```text
Chapter 1
-> Chapter 2
-> Chapter 3
-> Chapter 4
```

The test must produce a Continuity Report that separates:

* New canon
* Updated canon
* Still-known canon
* Invalidated canon
* Evidence for every change

This is the first V1 product demo target.

---

## Current Validation

The project currently validates with:

```text
pytest
ruff check .
mypy
```

All three must remain green after every hardening pass.
