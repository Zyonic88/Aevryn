# Aevryn Character Engine

## What Is It?

The Character Engine builds living character cards from Canon and Timeline.

It does not decide what is true.

It presents character-specific truth in a usable form.

## Why Does It Exist?

Creators need to know what a character looks like, carries, knows, feels, and where they are at a specific point in the story.

Static character cards are not enough for long-form stories.

Aevryn needs living cards that evolve as canon changes.

Example:

```text
Current Weapon: Iron Sword
Previous Weapon: Rusty Dagger
Valid From: Chapter 8
Evidence: Chapter 8, Scene 2
```

## What Authority Does It Own?

The Character Engine owns:

* Character card assembly
* Character-focused views of canon facts
* Character current state summaries
* Character historical state summaries
* Character relationships as they apply to character cards

It organizes character state for other systems.

V1 character cards can be built for a chapter or an exact scene position.

Scene-position cards must not include facts introduced later in the same chapter.

## V1 Rules

The Character Engine is a read layer.

It never mutates Canon or Timeline.

Character cards must be timeline-aware.

If a story position is requested explicitly, the position must exist in Timeline.

Previous values must come from Canon history order, not string ordering or display assumptions.

Unknown information remains absent or Unknown.

Character card visible names and fact values are whitespace-normalized for stable display.

Character card view models must reject malformed output:

* Character IDs are required and must be machine-safe.
* Display names are required.
* Fact attributes are required and must be machine-safe.
* Fact values are required.
* Fact dictionary keys must match their fact attributes.
* Valid-from source IDs must be machine-safe.

## What Does It NOT Own?

The Character Engine does not own:

* Canon fact storage
* Timeline validity windows
* Story import
* AI extraction
* Prompt generation
* Image generation
* Export formatting
* User accounts

It reads Canon and Timeline.

It does not replace them.

## How Does It Fail?

The Character Engine can fail if:

* A requested character does not exist in canon.
* A requested entity is not a character.
* A card treats unknown information as known.
* A card ignores timeline validity.
* A card mutates canon state.
* A scene-position card leaks facts introduced in a later scene.
* A card includes non-character authority that belongs to another engine.
* A card uses the latest character name when an earlier display-name fact is active.
* A card contains malformed IDs, blank visible values, or mismatched fact keys.

When character information is not supported by canon, the correct value is Unknown.

## How Does It Interact With Other Systems?

The Canon Engine provides evidence-backed facts and relationships.

The Timeline Engine provides current story position and validity windows.

The Scene Engine uses character cards to understand who is present and what state they are in.

The Prompt Engine eventually uses scene-ready character state to generate prompts.

The Export Engine can output character sheets built from Character Engine cards.
