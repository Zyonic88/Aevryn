# SceneSmith System Outline

## Purpose

SceneSmith is a Story Continuity Engine.

Its responsibility is to understand existing stories and maintain their current canonical state.

It is not a story generator.

It is not an image generator.

It is not a chatbot.

It is the source of truth for an evolving fictional world.

---

## Core Principle

A story is a living world.

Every chapter changes that world.

SceneSmith exists to remember those changes.

---

## System Architecture

SceneSmith is composed of the following major systems.

---

## Story Import System

Purpose:

Import source material.

Supports:

* TXT
* EPUB
* PDF
* DOCX
* Markdown
* Pasted chapters

Responsibilities:

* Parse documents
* Split chapters
* Split scenes
* Preserve chapter order

---

## Canon Engine

Purpose:

Maintain the current truth of the story.

Tracks:

* Characters
* Locations
* Buildings
* Organizations
* Items
* Weapons
* Skills
* Relationships
* Timeline

The Canon Engine becomes the authoritative state of the story.

---

## Character Engine

Purpose:

Maintain every character.

Tracks:

* Appearance
* Clothing
* Weapons
* Equipment
* Injuries
* Personality
* Relationships
* Status
* Current location

Outputs:

* Character Cards
* Character Timeline
* Character History

---

## World Engine

Purpose:

Maintain the evolving world.

Tracks:

* Cities
* Buildings
* Villages
* Kingdoms
* Weather
* Environment
* Ownership
* Damage
* Reconstruction

---

## Timeline Engine

Purpose:

Track story progression.

Tracks:

* Chapter
* Scene
* Event
* Character state
* World state

Allows reconstruction of the story at any point in time.

---

## Scene Engine

Purpose:

Generate scene context.

Outputs:

* Characters present
* Environment
* Time
* Weather
* Equipment
* Active relationships
* Current world state

---

## Prompt Engine

Purpose:

Generate production-ready prompts.

Outputs:

* AI Image Prompt
* Narration Prompt
* Camera Prompt
* Animation Prompt

Generated prompts always reference the current canonical state.

---

## Export Engine

Purpose:

Export data.

Formats:

* JSON
* Markdown
* CSV
* Character Sheets
* Scene Sheets
* Prompt Sheets

---

## System Flow

Import Story

↓

Analyze Story

↓

Extract Entities

↓

Update Canon

↓

Generate Scene Context

↓

Generate Prompts

↓

Export

---

## Core Rule

SceneSmith never invents canon.

Every extracted fact should contain:

* Source
* Evidence
* Confidence
* Current State

Unknown information remains Unknown until supported by evidence.

---

## Long-Term Goal

Create the world's most accurate Story Continuity Engine for AI-assisted storytelling.
