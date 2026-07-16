# AEVRYN_FUTURE_IDEAS.md

> Built by **Aetherra Labs**

This document is the official collection of future ideas for Aevryn.

These ideas are **not commitments**.

They exist to preserve concepts that may become future systems, modules, workflows, or quality-of-life improvements.

Ideas should remain separate from the official roadmap to prevent scope creep while ensuring valuable concepts are never lost.

---

# Design Philosophy

Ideas should follow Aevryn's existing architecture.

Future capabilities should consume Canon rather than replace it.

Every future feature should answer one question:

> Does this use Aevryn's understanding of the story better than simply sending text to an AI?

If the answer is no, it probably does not belong in Aevryn.

---

# Idea 001 - Narrative Perspective

## Summary

Allow creators to choose how generated writing is narrated.

This affects generated outputs only.

Canon remains unchanged.

## Possible Modes

* First Person
* Third Person Limited
* Third Person Omniscient
* Auto (Detect from imported story)

## Future Expansion

Additional narrative settings may include:

* Past / Present tense
* Narrative tone
* Reading level
* Prose density
* Dialogue emphasis
* Internal monologue frequency

These settings belong to project generation preferences rather than Canon.

---

# Idea 002 - Production Presets

## Summary

Allow creators to select predefined production workflows optimized for specific platforms or creative pipelines.

Production Presets influence Presentation, Prompt generation, and Export formatting without modifying Canon.

## Example Presets

### Platforms

* YouTube
* YouTube Shorts
* Facebook
* Instagram
* TikTok
* X
* Revid.ai

### Creative Workflows

* Manga Recap
* Manhwa Recap
* Audiobook
* Storyboard
* Visual Novel
* Comic
* Animation Pipeline

### AI Tool Presets

* Image Generation
* Video Generation
* Narration
* Voice Synthesis

## Example Revid.ai Preset

Automatically configures:

* Scene segmentation
* Prompt detail
* Character summaries
* Camera prompts
* Animation prompts
* Narration prompts
* Output formatting

---

# Idea 003 - Audiobook Production Engine

## Summary

Transform any imported story into a professionally narrated audiobook using Aevryn's understanding of the story rather than raw source text.

## Workflow

```text
Story Import
-> Canon
-> Timeline
-> Scene Engine
-> Scene Analyzer
-> Audiobook Engine
-> Voice Synthesis
-> Audiobook Export
```

## Features

### Voice Assignment

Assign persistent voices to:

* Narrator
* Characters
* Internal Monologue
* System Messages

### Pronunciation Dictionary

Maintain consistent pronunciation for:

* Character names
* Locations
* Skills
* Organizations
* Titles
* Foreign words

### Emotion-Aware Narration

Use Scene Analyzer output to automatically influence:

* Speaking speed
* Volume
* Intensity
* Pauses
* Emotional delivery

### Dialogue Mode

Support multiple speakers instead of a single narrator.

Each character may receive a unique voice.

### Optional Production Layers

* Ambient sound
* Music
* Chapter transitions
* Intro / Outro
* Cover artwork

### Export

* MP3
* WAV
* M4B
* Podcast packages
* Chapter markers

This engine consumes Canon-backed scene understanding and never modifies Canon itself.

---

# Idea 004 - Production Batching And Fair Usage Credits

## Summary

Allow creators to batch expensive production work such as image generation, video generation, voice synthesis, narration rendering, and multi-chapter media workflows.

This is future paid production scope.

It does not belong to Version 2 public beta.

## Product Boundary

Version 2 may expose scene-level Prompt Packs.

Version 2 should not generate images, videos, voices, or paid media outputs inside Aevryn.

Future production batching may allow creators to run:

* one scene
* one chapter
* selected scenes
* selected chapters
* up to a configured batch limit
* full production workflows when cost controls exist

## Monetization Principle

```text
Subscription pays for access.
Credits pay for expensive generation.
```

Subscriptions should cover Aevryn's core intelligence and platform workflow:

* projects
* imports
* Canon processing
* character sheets
* world sheets
* timeline views
* scene sheets
* prompt packs
* normal exports
* reasonable storage limits

Credits should be reserved for work with real variable provider or compute cost:

* image generation
* video generation
* voice synthesis
* narration rendering
* large production batches
* premium AI provider runs

## Fairness Rules

Core Aevryn workflow actions should not silently drain credits.

Paid plans should include monthly credits when media generation exists.

Extra credits should be optional.

Credit pricing should be based on actual provider cost, runtime cost, storage cost, and a reasonable margin.

Credit usage should be shown before a batch starts.

Failed provider calls should not charge users unless a provider has already charged Aetherra Labs and the policy clearly says so.

## Future Required Controls

Production batching requires:

* cost estimates before execution
* user confirmation before credit spend
* queueing
* retries
* cancellation
* batch progress
* provider failure handling
* generated asset storage
* usage history
* billing history
* abuse limits
* support visibility without exposing private manuscripts

This system must consume Canon, Prompt Packs, Production Presets, and user-approved generation settings.

It must not alter Canon.

---

# Future Ideas

Additional ideas will be appended here as they are developed.

Ideas are intentionally preserved even if they are years away from implementation.

Architecture and roadmap decisions remain separate from this document.
