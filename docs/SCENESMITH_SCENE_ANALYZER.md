# SceneSmith Scene Analyzer

## What Is It?

The Scene Analyzer understands what happened in a scene and why it matters.

It is not the Scene Engine.

The Scene Engine reconstructs current truth.

The Scene Analyzer explains scene meaning.

## Why Does It Exist?

Prompt generation needs more than raw chapter text and canon facts.

Creators need compact production context:

* Scene summary
* Purpose
* Conflict
* Mood
* Key events
* Character goals
* Character emotions
* Visual highlights
* Important objects
* Environment summary
* Changes introduced

Without Scene Analyzer, Prompt Engine is forced to work from too much raw source text.

That creates long, noisy prompt sheets instead of usable production packs.

## What Authority Does It Own?

Scene Analyzer owns:

* Scene summary
* Scene purpose
* Conflict description
* Emotional tone
* Visual highlights
* Character goals
* Character emotions
* Important objects
* Environment summary
* Changes introduced
* Continuity notes for production use
* Forbidden elements for prompt safety

It owns meaning-focused scene analysis.

## V1 Rules

The Scene Analyzer is deterministic.

It only analyzes a scene context whose snapshot points to the same scene.

Scene Analysis outputs must have a valid scene ID and non-empty summary, purpose, conflict, mood, and environment summary.

Scene Analysis list items must not be blank.

Scene Analysis list items must not repeat within the same output field.

It may compress accepted facts and relationships into human-readable meaning.

Its heuristic language must remain genre-neutral.

It may recognize broad beats such as challenges, contests, operations, preparation, resource pressure, command structure, and relationship tension when accepted facts support them.

It must not hard-code names, titles, power systems, factions, or genre-specific wording from a test story.

It must not name specific unsupported actors when Canon only supports a general conflict label.

Repeated facts, notes, and objects are deduplicated.

Retained canon becomes continuity notes.

Only facts evidenced by the current scene become changes introduced.

Mechanical metadata such as task rewards, penalties, and feasibility scores should not dominate production-facing summaries.

## What Does It NOT Own?

Scene Analyzer does not own:

* Canon truth
* Fact acceptance
* Entity extraction
* Story Import structure
* Timeline validity
* Character cards
* Prompt formatting
* Export formatting

It must use accepted canon and imported scene context.

It must not invent missing facts.

## How Does It Fail?

Scene Analyzer can fail if:

* It summarizes unsupported events.
* It changes story facts.
* It ignores accepted canon.
* It invents emotional states not supported by text or canon.
* It mistakes raw text for accepted truth.
* It produces vague summaries that cannot guide production.
* It allows prompt generation to re-dump the entire chapter.
* It treats retained canon as a newly introduced scene change.
* It analyzes a context whose snapshot does not match the scene.
* It emits blank production-facing analysis fields.
* It emits duplicate production-facing analysis rows.

When uncertain, it should return Unknown instead of guessing.

## How Does It Interact With Other Systems?

Scene Engine provides canon-backed scene context.

Scene Analyzer turns that context into a compact explanation of what the scene accomplishes.

Prompt Engine uses Scene Analyzer output to create production packs.

Export Engine can serialize Scene Analyzer output and production packs.

Canon remains the source of truth.

## Core Rule

Scene Engine answers:

```text
What is true right now?
```

Scene Analyzer answers:

```text
What happened, why does it matter, and how should production understand it?
```
