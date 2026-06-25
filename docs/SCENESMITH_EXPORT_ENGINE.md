# SceneSmith Export Engine

## What Is It?

The Export Engine converts SceneSmith data into external formats.

It outputs:

* JSON
* Markdown
* CSV
* Character Sheets
* Scene Sheets
* Prompt Sheets

It does not own the data it exports.

## Why Does It Exist?

Creators need to move SceneSmith context into other tools.

The Export Engine exists so Canon, Timeline, Character, Scene, and Prompt outputs can be used outside SceneSmith without changing the underlying state.

## What Authority Does It Own?

The Export Engine owns:

* Export formatting
* Text serialization
* Sheet-style output
* Stable external representations

It turns already-known state into portable output.

## V1 Rules

The Export Engine is deterministic.

It serializes existing objects only.

It never writes files directly.

It never changes Canon, Timeline, Scene, Prompt, or Presentation objects.

JSON output is stable and sorted.

CSV output uses stable headers.

Markdown output remains human-readable and does not mix unrelated formats.

Repeated Markdown list items are deduplicated.

Continuity Report exports include evidence context when available.

## What Does It NOT Own?

The Export Engine does not own:

* Canon facts
* Timeline validity
* Character card assembly
* Scene context assembly
* Prompt text generation
* File storage
* Database writes
* AI generation

It formats data.

It does not create or change data.

## How Does It Fail?

The Export Engine can fail if:

* It mutates source objects.
* It invents missing fields.
* It drops evidence.
* It produces unstable output ordering.
* It writes files without explicit file-handling authority.
* It mixes export formats in one output.
* It exports unstable ordering for facts, relationships, events, or state changes.
* It drops snapshot identifiers needed to trace exported scene context.
* It drops evidence context needed to audit continuity changes.

Unknown information should remain absent or represented as Unknown.

## How Does It Interact With Other Systems?

The Character Engine provides character cards.

The Scene Engine provides scene context.

The Prompt Engine provides prompt bundles.

The Export Engine serializes those objects into external formats.

Future file-writing behavior should be handled explicitly and separately.
