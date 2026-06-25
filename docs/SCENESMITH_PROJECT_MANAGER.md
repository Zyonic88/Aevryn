# SceneSmith Project Manager

## What Is It?

The Project Manager coordinates SceneSmith workflows for a local project.

It is not the Canon Engine.

It is not Story Import.

It is not extraction.

It is not export.

It is the orchestration layer that asks the existing systems to do their jobs in the correct order.

## Why Does It Exist?

SceneSmith needs one place that can run a complete proof workflow:

```text
Import Story
-> Extract Candidates
-> Update Canon
-> Build Character Cards
-> Build Scene Context
-> Build Prompts
-> Export
```

Without the Project Manager, the CLI and future interfaces would duplicate orchestration logic.

The Project Manager keeps the workflow reusable without giving interface code authority over canon truth.

## What Authority Does It Own?

The Project Manager owns:

* Workflow ordering
* Project-level command coordination
* Choosing which existing system is called next
* Passing imported source data into extraction
* Passing accepted extraction results into Canon Updating
* Passing Canon-backed state into Character, Scene, Prompt, and Export workflows
* Building Continuity Reports from accepted Canon update summaries

It may decide:

* Which source file is being processed
* Which scene is being requested
* Which character card is being requested
* Which output bundle should be assembled
* Which completed project run should be summarized as a Continuity Report

## V1 Rules

The Project Manager is orchestration only.

It never decides canon truth.

It never rewrites extraction candidates.

It rejects imported sources that contain no scenes.

Single-scene extraction must return candidates for the requested scene.

Multi-scene AI candidate envelopes must include exactly one payload for every imported scene.

Repeated selected IDs are deduplicated before downstream view construction.

Continuity Reports separate new, updated, still-known, and invalidated Canon records.

Continuity Report records include evidence ID, chapter ID, scene ID, and evidence quote when Canon has them.

Downstream errors should remain visible instead of being hidden.

## What Does It NOT Own?

The Project Manager does not own:

* Canon truth
* Entity extraction rules
* Evidence validation
* Chapter parsing
* Scene splitting
* Timeline state validity
* Character card content
* Scene context content
* Prompt wording rules
* Export formatting
* Persistent storage
* AI decisions

If it needs information, it asks the owning system.

## How Does It Fail?

The Project Manager can fail when:

* A source file cannot be read
* Story Import rejects empty or invalid input
* Extraction returns invalid evidence anchors
* Canon Updating rejects low-confidence candidates
* A requested character is unknown
* A requested scene is unknown
* A downstream engine raises a validation error
* An extractor returns candidates for the wrong scene
* An imported source contains no chapters or scenes
* A multi-scene AI candidate envelope is missing scenes or references unknown scenes

It should fail loudly and preserve the original error context.

It should not silently invent missing characters, scenes, evidence, or canon state.

## How Does It Interact With Other Systems?

The Project Manager asks Story Import to parse source files.

It asks Entity Extraction to produce candidates.

It asks Canon Updating to validate and apply accepted candidates.

It asks the Canon Database for accepted truth indirectly through Character and Scene systems.

It asks the Character Engine for character cards.

It asks the Scene Engine for scene context.

It asks the Prompt Engine for prompt bundles.

It asks the Export Engine to serialize results.

## Core Rule

The Project Manager coordinates.

It does not decide truth.

If a fact is not accepted by Canon, the Project Manager must treat it as unknown.
