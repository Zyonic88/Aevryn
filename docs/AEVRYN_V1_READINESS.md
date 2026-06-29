# Aevryn V1 Readiness

> Built by **Aetherra Labs**

This document tracks whether each Version 1 system is documented, implemented, tested, and usable through the proof workflow.

Acceptance is governed by `docs/AEVRYN_V1_ACCEPTANCE_CRITERIA.md`.

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
| Story Import | V1 Complete \(V1.1\) | Imports TXT, Markdown, HTML, FB2, DOCX, ODT, and EPUB through deterministic adapters, fails clearly for deferred PDF/MOBI/AZW3 parser support, parses chapters/scenes, derives readable paragraphs from oversized unspaced source blocks, creates paragraph and sentence evidence anchors, keeps paragraph indexes unique inside each scene, validates anchor chapter/scene ownership and anchor indexes against referenced paragraphs/sentences, preserves decimals/titles/numbered names during sentence splitting, repairs common encoding artifacts, supports numbered web-novel headings, rejects out-of-order explicit multi-chapter imports, and logs import summaries. |
| Translation Engine | Foundation Only | Documented boundary. Optional for V1 and not required to prove continuity. |
| Entity Extraction | V1 Complete \(RC1\) | Evidence-bounded extraction validates full AI payload shape, requires decoded strict JSON text, rejects duplicate JSON keys, non-standard JSON constants, and unsupported fields, validates confidence range, requires scene anchors, rejects duplicate candidate identities at the model boundary, normalizes human-readable candidate text, and logs candidate counts. |
| Canon Updating | V1 Complete \(RC1\) | Accepts/rejects candidates using confidence, evidence, known-entity checks, unique evidence anchors, same-scene evidence validation, and paragraph/sentence ordering for replacement facts; summary IDs cannot be both accepted and rejected; generic non-character entities are stored explicitly; duplicate entity versions and duplicate semantic relationships are idempotent. |
| Canon Engine | V1 Complete \(RC1\) | Stores evidence-backed truth, relationships, state changes, and generic entities; rejects conflicting reused permanent IDs, facts for unknown entities, relationships with unknown endpoints, mismatched timeline evidence, backward validity windows, and same-position replacement windows; keeps duplicate updates idempotent and retrieves current facts by timeline order instead of ID order. |
| Timeline Engine | V1 Complete \(RC1\) | Tracks chapters, scenes, events, state changes, and story position; rejects overlapping validity windows, mismatched state-change event positions, duplicate state-change conflicts, conflicting ID reuse, and returns deterministic story-order history. |
| Character Engine | V1 Complete \(RC1\) | Builds living character cards from Canon and Timeline; rejects non-character and unknown entities, validates explicit story positions, preserves unknowns, uses active display-name facts, normalizes visible card text, and derives previous values from timeline-ordered Canon history. |
| World Engine | V1 Complete \(RC1\) | Builds deterministic world-state views from Canon; rejects character entities, validates relationship endpoints, preserves evidence references, uses active display-name facts, normalizes visible world-state text, and remains a read layer. |
| Scene Engine | V1 Complete \(RC1\) | Builds deterministic canon-backed scene context; validates scene positions through Timeline, prevents future fact and relationship leakage, uses genre-neutral scene-relevance categories, rejects duplicate snapshot reference IDs, deduplicates repeated inputs, returns relationships in stable order, and includes related location IDs when relationships prove them. |
| Scene Analyzer | V1 Complete \(RC1\) | Produces deterministic scene meaning, mood, purpose, visual highlights, and continuity notes; validates snapshot/scene consistency, recognizes broad genre-neutral beats such as challenges, contests, operations, group structure, resource pressure, and relationship tension from accepted facts, avoids unsupported named conflict claims, normalizes and deduplicates repeated outputs, and separates retained canon from newly introduced changes. |
| Prompt Engine | V1 Complete \(RC1\) | Builds deterministic prompt bundles and production packs from scene context and analysis; uses scene-relevant character facts instead of dumping full living character cards, normalizes production-pack rows, deduplicates repeated lines, shortens long analysis text, avoids raw chapter dumps, and never calls external AI tools. |
| Presentation Engine | V1 Complete \(RC1\) | Builds deterministic human-readable character, scene, world, and production pack views; validates scene/analysis alignment, groups character profile sections with genre-neutral attribute categories, normalizes visible section whitespace, deduplicates repeated display items, removes prompt placeholders, shortens long prompt lines, and remains separate from Export. |
| Export Engine | V1 Complete \(RC1\) | Exports machine and presentation outputs to deterministic JSON, Markdown, and CSV; sorts exported facts, relationships, events, and state changes, includes complete scene snapshot identifiers, exports machine-readable world state JSON, keeps Continuity Report JSON audit-complete, summarizes retained/state-change noise in Markdown, normalizes and deduplicates Markdown lists, and never writes files directly. |
| Project Manager | V1 Complete \(RC1\) | Coordinates import, extraction, canon update, character cards, scene context, prompts, world state, and Continuity Reports; rejects empty imported sources, validates single-scene extractor output, validates multi-scene AI candidate envelopes, deduplicates selected IDs, and stays orchestration-only. |
| CLI Proof Workflow | V1 Complete \(RC1\) | Supports import, extraction prompt, single-scene and multi-scene AI JSON application, character, scene, prompt, world, continuity, and validation commands; exposes imported chapter and scene IDs plus bounded evidence-anchor previews, defaults scene and prompt views to accepted characters in the selected scene, shows defaults in subcommand help, reports expected workflow errors to stderr with exit code 1, gives recovery hints for common unknown scene/entity selections, deduplicates repeated selected IDs, supports validation case listing, focused case runs, compact validation summaries, machine-readable validation output, deterministic validation snapshots, and keeps orchestration in Project Manager. |
| Web Import | Documented Only | V1 should prefer manual upload/paste until permission and rate-limit handling are implemented. |

---

## RC1 Evidence

Implemented V1 systems are complete for RC1.

* Logging policy is documented and tested in `docs/AEVRYN_LOGGING_POLICY.md`.
* Acceptance checklists are now tracked in `docs/AEVRYN_V1_ACCEPTANCE_AUDIT.json`.
* Continuity Report exists and is split by intent: JSON preserves the audit trail, Markdown presents a concise human view.
* CLI output formats are split by intent: Markdown is presentation-first, while JSON and CSV preserve machine-readable detail.
* Chapter 1 -> Chapter 10 continuity validation has been run with saved generated outputs.
* A second-genre Chapter 1 -> Chapter 10 validation has been run with saved generated outputs to guard against building around one novel.
* Eight-genre validation corpus now covers 80 local chapter files, 80 extraction-ready scene inputs, evidence-bounded extraction prompt digests, and 8,828 evidence anchors without storing chapter text in git.
* Validation output is guarded against raw chapter text and extraction prompt leakage.
* Validation snapshots can be written with `aevryn validate --snapshot-dir <path>` and refuse to overwrite non-empty directories.
* Validation source roots are configurable through `--source-root` or `AEVRYN_VALIDATION_ROOT`, with explicit CLI arguments taking priority.
* Validation fingerprint documentation is checked against the checked-in case metadata.
* Generated snapshot artifact directories are ignored by git while `snapshots/README.md` remains trackable.
* Validation runner logging now records suite start, suite completion, failed cases, suite digest, and elapsed milliseconds without changing deterministic CLI output.
* Performance baseline policy is documented in `docs/AEVRYN_PERFORMANCE_BASELINE.md`.
* Canon Rebuild validation now covers byte-deterministic rebuilds, incremental convergence, and out-of-order source rejection in automated tests.
* Final RC snapshot comparison passed using two fresh validation snapshots.
* Compared snapshot base: `snapshots/v1_rc1_validation_comparison_20260626_014637`.

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

After subsystem acceptance, Aevryn must run a continuity test across:

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
ruff check pyproject.toml docs src tests validation
mypy src tests
aevryn validate --summary-only
```

All commands must remain green after every hardening pass.

The current validation corpus fingerprint is:

```text
cases=8 passed=8 failed=0 files=80 chapters=80 scenes=80 paragraphs=2294 sentences=8828 anchors=8828
extraction_inputs=80 extraction_anchors=8828
digest=1a04733548822f82afc473a468cf6a6189387cb97eb915cc803d6b6e94b5d749
```
