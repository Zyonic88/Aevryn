# SceneSmith Architecture

## What Is It?

SceneSmith is an AI-powered Story Continuity Engine built by Aetherra Labs.

Its architecture is intentionally simple:

```text
SceneSmith
|
+-- Story Import
+-- Canon Engine
+-- Character Engine
+-- World Engine
+-- Timeline Engine
+-- Scene Engine
+-- Prompt Engine
+-- Export Engine
+-- Project Manager
```

No unnecessary complexity.

## Why Does It Exist?

SceneSmith exists to help creators maintain continuity across long-form stories.

The architecture separates responsibilities so each system owns one clear part of the story-continuity workflow.

The goal is not to generate story.

The goal is to understand the story that already exists and keep its current state accurate.

## What Authority Does It Own?

The architecture owns the boundaries between SceneSmith systems.

It defines which systems exist, why they exist, and where their authority begins and ends.

The high-level systems are:

* Story Import
* Canon Engine
* Character Engine
* World Engine
* Timeline Engine
* Scene Engine
* Prompt Engine
* Export Engine
* Project Manager

## What Does It NOT Own?

The architecture document does not own implementation details.

It does not define:

* Database schema
* Extraction algorithms
* Prompt templates
* User interface behavior
* Deployment strategy
* Payment systems
* User accounts

Those details belong in later subsystem documents only when they are needed.

## How Does It Fail?

The architecture fails if:

* A system has unclear authority.
* Two systems own the same responsibility.
* A system does more than one unrelated job.
* Feature work begins before the subsystem purpose is documented.
* Canon state can be changed without evidence.
* Prompt generation starts guessing instead of reading canon.

When authority is unclear, the correct next step is documentation, not code.

## How Does It Interact With Other Systems?

This document governs the system map.

Every subsystem document must answer:

* What is it?
* Why does it exist?
* What authority does it own?
* What does it NOT own?
* How does it fail?
* How does it interact with other systems?

Implementation work should follow those documents, not replace them.

## System Responsibilities

### Story Import

Purpose:

Read story.

Supports:

* TXT
* EPUB
* PDF
* DOCX
* Copied chapters

Nothing else.

### Canon Engine

This is the heart.

Not AI.

The database of truth.

Example:

```text
Mark

Current Weapon:
Steel Sword

Previous:
Rusty Dagger

Chapter Changed:
14

Confidence:
High

Evidence:
Chapter 14 paragraph 6
```

Every entity gets this treatment.

Characters.

Items.

Locations.

Buildings.

Organizations.

### Timeline Engine

Tracks:

* Chapter
* Scene
* Event
* Current State

Not history for history's sake.

Current truth.

### Character Engine

This becomes SceneSmith's famous character cards.

But they evolve.

Not static cards.

Living cards.

### World Engine

Tracks:

* Weather
* Cities
* Castles
* Forests
* Battle damage
* Ownership

The world itself changes.

### Scene Engine

This is the money-maker.

Given Scene 148, it automatically knows:

* Who
* Where
* When
* Environment
* Equipment
* Current injuries
* Mood
* Relevant objects

### Prompt Engine

This generates:

* Image prompts
* Narration prompts
* Camera prompts
* Animation prompts

Not from guesses.

From canon.

### Export Engine

Outputs:

* Revid
* JSON
* Markdown
* CSV
* Character Sheets
* Scene Sheets
* Prompt Sheets
