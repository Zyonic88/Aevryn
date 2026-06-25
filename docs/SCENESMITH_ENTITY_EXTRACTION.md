# SceneSmith Entity Extraction

## What Is It?

Entity Extraction proposes story entities and relationships from imported scenes.

This is the first phase where AI is allowed to participate.

The AI owns extraction.

The Canon owns truth.

## Why Does It Exist?

SceneSmith needs a way to turn source text into candidate facts without making AI responsible for memory or truth.

Entity Extraction reads imported scene structure and proposes:

* Characters
* Locations
* Items
* Facts
* Relationships
* State changes

Every proposal must point back to an evidence anchor from Story Import.

## What Authority Does It Own?

Entity Extraction owns:

* Sending scene text to an extractor
* Receiving extracted candidates
* Preserving evidence anchor references
* Preserving confidence
* Rejecting candidates that cite unknown anchors
* Rejecting candidates with invalid confidence
* Returning extraction results for review or canon update

It owns candidates.

It does not own canon.

## What Does It NOT Own?

Entity Extraction does not own:

* Canon truth
* Canon updates
* Story Import structure
* Timeline validity
* Character cards
* Scene context
* Prompt generation
* Export formatting

The AI never writes directly to Canon.

## How Does It Fail?

Entity Extraction can fail if:

* A candidate has no evidence anchor.
* A candidate has no confidence score.
* A candidate cites evidence outside the current scene.
* A candidate is treated as canonical truth.
* A candidate references a scene that was not imported.
* The extractor invents unsupported details.
* Canon is updated without validation.

Extraction failure should produce rejected or absent candidates, not canon changes.

## How Does It Interact With Other Systems?

Story Import provides scenes and evidence anchors.

Entity Extraction proposes candidates from those anchors.

Canon Updating later decides whether candidates become canon.

Canon Database stores accepted truth.

Character, Scene, Prompt, and Export systems only use accepted canon, not raw extraction candidates.

## First AI Extraction Milestone

Input:

* One imported scene
* Paragraph and sentence evidence anchors

Output:

* Candidate entities
* Candidate facts
* Candidate relationships
* Candidate state changes

Every candidate must include:

* Evidence anchor
* Confidence

Unsupported claims are omitted.

Unknown information remains Unknown.

## Core Rule

AI may propose.

Canon decides.
