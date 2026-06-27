# Aevryn Architecture

## What Is It?

Aevryn is an AI-powered Story Continuity Engine built by Aetherra Labs.

Its architecture is intentionally simple:

```text
Aevryn
|
+-- Story Import
+-- Web Import
+-- Translation Engine
+-- Canon Engine
+-- Character Engine
+-- World Engine
+-- Timeline Engine
+-- Scene Engine
+-- Scene Analyzer
+-- Prompt Engine
+-- Presentation Engine
+-- Export Engine
+-- Project Manager
```

No unnecessary complexity.

## Why Does It Exist?

Aevryn exists to help creators maintain continuity across long-form stories.

The architecture separates responsibilities so each system owns one clear part of the story-continuity workflow.

The goal is not to generate story.

The goal is to understand the story that already exists and keep its current state accurate.

## What Authority Does It Own?

The architecture owns the boundaries between Aevryn systems.

It defines which systems exist, why they exist, and where their authority begins and ends.

The high-level systems are:

* Story Import
* Web Import
* Translation Engine
* Canon Engine
* Character Engine
* World Engine
* Timeline Engine
* Scene Engine
* Scene Analyzer
* Prompt Engine
* Presentation Engine
* Export Engine
* Project Manager

Each system has a dedicated system document in `docs/`.

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

After Story Import is documented and implemented, the architecture should be treated as frozen.

No new systems should be added without deliberate architecture review.

## System Responsibilities

### Story Import

Purpose:

Read story and create stable source structure.

Supports:

* TXT
* Markdown
* HTML
* FB2
* DOCX
* ODT
* EPUB
* Copied chapters

Deferred until dedicated parser support:

* PDF
* MOBI
* AZW3

Owns:

* Chapter parsing
* Scene splitting
* Paragraph indexing
* Source references
* Chapter IDs
* Scene IDs
* Evidence anchors

Nothing else.

### Web Import

Purpose:

Accept URLs as source intake only when import is allowed.

Owns:

* URL intake
* Metadata extraction
* Chapter discovery
* Source attribution
* Import permission checks
* Robots.txt checks
* Rate-limit policy

Does not own:

* Canon truth
* AI extraction
* Copyright bypass
* Paywall bypass
* Prompt generation

For V1, manual upload and paste remain the primary path.

Web Import should fail closed when permissions are unclear.

### Translation Engine

Purpose:

Translate or normalize imported source text while preserving canon continuity.

Owns:

* Translation workflow
* Glossary and term-bank checks
* Name preservation
* Alias detection
* Title and honorific handling
* Sentence restructuring
* Translation-to-source evidence links

Does not own:

* Canon truth
* Entity extraction
* Story Import structure
* Timeline validity
* Prompt generation

For V1, Translation is optional.

It may run after Story Import and before Entity Extraction.

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

This becomes Aevryn's famous character cards.

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

### Scene Analyzer

Purpose:

Understand what a scene accomplishes.

Outputs:

* Scene summary
* Purpose
* Conflict
* Mood
* Visual highlights
* Character goals
* Character emotions
* Important objects
* Environment summary
* Changes introduced
* Continuity notes

Scene Analyzer does not own canon truth.

### Prompt Engine

This generates:

* Image prompts
* Narration prompts
* Camera prompts
* Animation prompts

Not from guesses.

From canon.

### Presentation Engine

Purpose:

Convert internal truth into clean human-readable views.

Outputs:

* Character Profiles
* Scene Sheets
* World Sheets
* Timeline Views
* Relationship Graphs
* Continuity Reports
* Prompt Pack Views

Presentation does not own truth.

Presentation creates the view model.

Export writes it.

### Export Engine

Outputs:

* Revid
* JSON
* Markdown
* CSV
* Character Sheets
* Scene Sheets
* Prompt Sheets

## Product Constraint

Aevryn must prove the engine before the interface.

Do not build a website, login system, payment system, subscription system, AI chat, or image generation workflow until the evidence-backed scene reconstruction pipeline works through CLI or another minimal terminal workflow.
