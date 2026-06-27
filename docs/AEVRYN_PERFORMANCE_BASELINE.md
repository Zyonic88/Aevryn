# Aevryn Performance Baseline

> Built by **Aetherra Labs**

This document defines the V1 performance baseline policy.

Performance measurement must not break deterministic validation output.

## V1 Rule

Aevryn may log runtime metrics, but golden outputs and validation snapshots must remain stable for byte comparison.

Do not write elapsed time, timestamps, machine paths, or environment-specific values into deterministic exports.

## Current Baseline Surface

The validation runner logs:

* `validation_suite_started`
* `validation_suite_completed`

The completion log includes:

* Case count
* Passed count
* Failed count
* Suite digest
* Elapsed milliseconds

The CLI output intentionally omits elapsed time.

## Current Corpus Size

The V1 validation corpus currently covers:

* 8 genres
* 80 chapter files
* 80 imported chapters
* 80 scenes
* 2,294 paragraphs
* 8,828 sentences
* 8,828 evidence anchors

## Regression Rule

If validation becomes noticeably slower, investigate before adding new features.

Performance hardening belongs in V1 when it improves:

* Import speed
* Validation speed
* Extraction-readiness speed
* Export speed
* Memory use
* Deterministic rebuild reliability

Performance work must not weaken evidence, canon, timeline, or validation correctness.
