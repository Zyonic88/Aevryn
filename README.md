# Aevryn

> **AI-Powered Story Continuity Engine**
>
> Built by **Aetherra Labs**
>
> Primary domain: **https://aevryn.ai**

Upload a story. Aevryn builds a living canon that stays consistent across
every chapter.

**Evidence in. Canon out.**

## Overview

Aevryn is an AI-powered Story Continuity Engine designed for creators who
work with novels, manga, manhwa, web novels, comics, scripts, and other
long-form stories.

Its purpose is not to generate stories.

Its purpose is to understand existing stories.

Aevryn continuously analyzes chapters, tracks characters, locations, items,
relationships, timeline progression, and world state, building a living canon
database that evolves alongside the story.

This enables creators to generate consistent scene descriptions, prompt packs,
narration prompts, and future AI-assisted media without continuity errors.

## Why Not Just ChatGPT?

ChatGPT can answer from a prompt.

Aevryn maintains evidence-backed story state.

Instead of asking an AI to remember everything every time, Aevryn imports
story evidence, accepts or rejects extracted candidates, versions canon changes,
and reconstructs what was true at a specific chapter or scene.

That is the difference:

```text
Story evidence
-> Candidate facts
-> Canon validation
-> Timeline-aware continuity
-> Human-readable production outputs
```

## Current Status

Aevryn is currently **V1 Engine Complete** for the terminal-based story
continuity workflow.

V1 understands story structure, evidence anchors, candidate extraction payloads,
canon updates, timeline-aware scene state, character sheets, world sheets,
continuity reports, prompt packs, deterministic exports, and validation runs.

V1 does **not** include a website, accounts, payments, cloud sync, image
generation, video generation, or AI chat.

## Trust Signals

Final V1 acceptance validation:

* V1 Engine Complete
* Final V1 acceptance sweep passed
* 677 automated tests passing
* 118 frontend tests passing
* Deterministic rebuild validation
* Cross-genre validation
* 8-genre validation corpus
* 80 local chapter files
* 8,828 evidence anchors
* Evidence-backed canon
* Timeline-aware continuity
* V1 architecture complete
* Validation score: 100%

Final V1 acceptance snapshot:

```text
snapshots/v1_final_acceptance_20260626_122543
```

Current validation digest:

```text
ecd12849eeeaf8f9638a6c77b3e3dbb7c4a0dc0cd29fd869983e85dd5e88d69c
```

---

## The Problem

Current AI-assisted recap and storytelling workflows suffer from major continuity problems.

Characters suddenly change appearance.

Weapons disappear.

Buildings revert to earlier states.

Dead characters reappear.

AI has no persistent understanding of the story.

Every prompt starts almost from scratch.

---

## The Solution

Aevryn creates a continuously evolving Story State.

Instead of asking AI to remember everything every time, Aevryn maintains the
current canonical truth.

Every generated prompt references the latest known state of the story.

---

## Core Features

* Story analysis
* Character tracking
* Relationship tracking
* Equipment tracking
* Inventory tracking
* Location tracking
* Building and environment tracking
* Timeline management
* Canon database
* Character card generation
* Scene breakdown
* Canon-backed prompt pack generation
* Narration prompt generation
* Export to external tools

---

## V1 CLI Quickstart

Install the project in editable mode:

```powershell
pip install -e .[dev]
```

Inspect a text chapter import:

```powershell
aevryn import path\to\chapter_001.txt --source-id my_story
```

The import command prints chapter IDs, scene IDs, a scene map, and a bounded
evidence-anchor preview. Use scene IDs with `--scene-id` to inspect
timeline-safe character, scene, world, and prompt views.

Generate the evidence-bounded extraction prompt for one scene:

```powershell
aevryn extraction-prompt path\to\chapter_001.txt --source-id my_story
```

Apply an AI extraction response from JSON:

```powershell
aevryn extract-ai-json path\to\chapter_001.txt path\to\ai_response.json --source-id my_story
```

The command prints accepted and rejected candidate counts plus stable accepted
IDs, such as `accepted_entity_ids`. Use those IDs in follow-up commands like
`character`, `scene`, `world`, and `prompt`.

Generate canon-backed outputs from that response:

```powershell
aevryn character path\to\chapter_001.txt --source-id my_story --ai-response-file path\to\ai_response.json --character-id character_mark
aevryn scene path\to\chapter_001.txt --source-id my_story --ai-response-file path\to\ai_response.json
aevryn prompt path\to\chapter_001.txt --source-id my_story --ai-response-file path\to\ai_response.json
aevryn continuity path\to\chapter_001.txt --source-id my_story --ai-response-file path\to\ai_response.json
```

Markdown output is presentation-first for quick scanning. JSON and CSV outputs
preserve machine-readable detail for audits, tests, and downstream tools.

Run the validation corpus:

```powershell
aevryn validate --summary-only
```

The default validation source root is:

```text
~/Desktop/Aevryn test chapters
```

Use `--source-root` or `AEVRYN_VALIDATION_ROOT` to point validation at a
different local corpus.

Create a deterministic validation snapshot:

```powershell
aevryn validate --summary-only --snapshot-dir snapshots/my_run
```

Snapshot artifact directories are ignored by git. They store deterministic
validation metadata only, not chapter text.

---

## Development Checks

Run these before committing:

```powershell
ruff check pyproject.toml docs src tests validation
mypy src tests
pytest -q
aevryn validate --summary-only
```

---

## Design Philosophy

Aevryn never invents canon.

Every extracted fact should include:

* Evidence
* Source Chapter
* Confidence
* Current Status

If evidence does not exist, the system records the information as Unknown rather than hallucinating details.

---

## Long-Term Vision

Aevryn aims to become the industry's most accurate AI-powered story continuity platform.

The long-term goal is to allow creators to upload an entire story and immediately begin producing canonically accurate AI-assisted content with minimal manual work.

---

Built by Aetherra Labs.
