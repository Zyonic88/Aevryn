# SceneSmith

> **AI-Powered Story Continuity Engine**
>
> Built by **Aetherra Labs**

Upload a story. SceneSmith builds a living canon that stays consistent across
every chapter.

**Evidence in. Canon out.**

## Overview

SceneSmith is an AI-powered Story Continuity Engine designed for creators who
work with novels, manga, manhwa, web novels, comics, scripts, and other
long-form stories.

Its purpose is not to generate stories.

Its purpose is to understand existing stories.

SceneSmith continuously analyzes chapters, tracks characters, locations, items,
relationships, timeline progression, and world state, building a living canon
database that evolves alongside the story.

This enables creators to generate consistent scene descriptions, prompt packs,
narration prompts, and future AI-assisted media without continuity errors.

## Why Not Just ChatGPT?

ChatGPT can answer from a prompt.

SceneSmith maintains evidence-backed story state.

Instead of asking an AI to remember everything every time, SceneSmith imports
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

SceneSmith is currently a **V1 Release Candidate** focused on proving the
continuity engine in the terminal.

V1 understands story structure, evidence anchors, candidate extraction payloads,
canon updates, timeline-aware scene state, character sheets, world sheets,
continuity reports, prompt packs, deterministic exports, and validation runs.

V1 does **not** include a website, accounts, payments, cloud sync, image
generation, video generation, or AI chat.

## Trust Signals

Current RC1 validation:

* 458 automated tests passing
* Deterministic rebuild validation
* Cross-genre validation
* 7-genre validation corpus
* 70 local chapter files
* 7,578 evidence anchors
* Evidence-backed canon
* Timeline-aware continuity
* RC1 architecture complete
* Validation score: 100%

Current validation digest:

```text
816f6226832fe56ccdddc4064630807d31dd3646d4ec4573fde1450d0c2a3aad
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

SceneSmith creates a continuously evolving Story State.

Instead of asking AI to remember everything every time, SceneSmith maintains the
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
scenesmith import path\to\chapter_001.txt --source-id my_story
```

Generate the evidence-bounded extraction prompt for one scene:

```powershell
scenesmith extraction-prompt path\to\chapter_001.txt --source-id my_story
```

Apply an AI extraction response from JSON:

```powershell
scenesmith extract-ai-json path\to\chapter_001.txt path\to\ai_response.json --source-id my_story
```

The command prints accepted and rejected candidate counts plus stable accepted
IDs, such as `accepted_entity_ids`. Use those IDs in follow-up commands like
`character`, `scene`, `world`, and `prompt`.

Generate canon-backed outputs from that response:

```powershell
scenesmith character path\to\chapter_001.txt --source-id my_story --ai-response-file path\to\ai_response.json --character-id character_mark
scenesmith scene path\to\chapter_001.txt --source-id my_story --ai-response-file path\to\ai_response.json
scenesmith prompt path\to\chapter_001.txt --source-id my_story --ai-response-file path\to\ai_response.json
scenesmith continuity path\to\chapter_001.txt --source-id my_story --ai-response-file path\to\ai_response.json
```

Run the validation corpus:

```powershell
scenesmith validate --summary-only
```

The default validation source root is:

```text
~/Desktop/SceneSmith test chapters
```

Use `--source-root` or `SCENESMITH_VALIDATION_ROOT` to point validation at a
different local corpus.

Create a deterministic validation snapshot:

```powershell
scenesmith validate --summary-only --snapshot-dir snapshots/my_run
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
scenesmith validate --summary-only
```

---

## Design Philosophy

SceneSmith never invents canon.

Every extracted fact should include:

* Evidence
* Source Chapter
* Confidence
* Current Status

If evidence does not exist, the system records the information as Unknown rather than hallucinating details.

---

## Long-Term Vision

SceneSmith aims to become the industry's most accurate AI-powered story continuity platform.

The long-term goal is to allow creators to upload an entire story and immediately begin producing canonically accurate AI-assisted content with minimal manual work.

---

Built by Aetherra Labs.
