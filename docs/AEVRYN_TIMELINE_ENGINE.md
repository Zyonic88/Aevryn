# Aevryn Timeline Engine

## What Is It?

The Timeline Engine manages story position and state history.

The Canon Engine stores truth.

The Timeline Engine tells Aevryn when that truth is valid.

Example:

```text
Chapter 1: Mark has rusty dagger
Chapter 8: Mark buys iron sword
Chapter 20: Mark loses iron sword
```

With timeline authority, Aevryn can answer:

```text
What should Mark look like in Scene 14?
```

## Why Does It Exist?

Aevryn's value depends on continuity at a specific point in the story.

A fact is not enough by itself.

Aevryn also needs to know:

* When the fact becomes true
* When the fact stops being true
* Which chapter and scene contain the change
* What the current story position is

Once Canon and Timeline are functional, Character Cards become meaningful.

Example:

```text
Current Weapon: Iron Sword
Previous Weapon: Rusty Dagger
Valid From: Chapter 8
Evidence: Chapter 8, Scene 2
```

## What Authority Does It Own?

The Timeline Engine owns:

* Chapters
* Scenes
* Events
* State changes
* valid_from
* valid_until
* Current story position

It manages story order and validity windows.

## V1 Rules

The Timeline Engine is deterministic.

Given the same chapters, scenes, events, and state changes, it must always return the same order and active state.

One subject attribute may have only one active value at a story position.

Adjacent validity windows are allowed.

Overlapping validity windows are rejected.

Permanent timeline IDs are never silently reused for different data.

Chapter and scene positions are one-based.

Boolean values are not valid chapter or scene positions.

Timeline machine fields are whitespace-free tokens:

* Event IDs
* State-change IDs
* Subject IDs
* State attributes
* Linked event IDs

Filtered Timeline lookups must validate their filters.

Event position filters must point to registered scenes.

State-change event links must point to an event at the same valid_from position.

State-history subject and attribute filters must be machine-safe tokens.

## What Does It NOT Own?

The Timeline Engine does not own:

* Character extraction
* Canon fact storage
* Prompt generation
* Image generation
* Export formatting
* Story generation
* User interface behavior

It does not decide what is true.

It decides when a recorded truth is valid.

## How Does It Fail?

The Timeline Engine can fail if:

* Chapters are registered out of order without detection.
* Scenes are attached to the wrong chapter.
* Events are recorded without a valid story position.
* State changes do not have valid_from.
* State changes overlap incorrectly.
* A state change references an event from a different story position.
* valid_until is earlier than valid_from.
* Current story position points to a chapter or scene that does not exist.
* A state-change ID is reused for different data.
* Timeline IDs or attributes contain whitespace.
* A filtered lookup uses an unknown story position or malformed subject/attribute token.

When a position is unknown, the Timeline Engine should reject the operation instead of guessing.

## How Does It Interact With Other Systems?

The Canon Engine stores evidence-backed facts.

The Timeline Engine stores when those facts are valid.

The Character Engine reads Canon and Timeline together to build living character cards.

The Scene Engine asks Timeline for the target story position, then asks Canon for the valid state at that position.

The Prompt Engine receives scene-ready state from the Scene Engine.

The Export Engine can output timeline-backed state histories.

## V1 Build Order

1. Canon Engine
2. Timeline Engine
3. Character Engine
4. Scene Engine
5. Prompt Engine
6. Export Engine
