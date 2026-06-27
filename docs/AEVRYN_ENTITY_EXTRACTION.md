# Aevryn Entity Extraction

## What Is It?

Entity Extraction proposes story entities and relationships from imported scenes.

This is the first phase where AI is allowed to participate.

The AI owns extraction.

The Canon owns truth.

## Why Does It Exist?

Aevryn needs a way to turn source text into candidate facts without making AI responsible for memory or truth.

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
* Enforcing the candidate payload schema
* Rejecting duplicate JSON keys in AI responses
* Preserving evidence anchor references
* Preserving confidence
* Rejecting candidates that cite unknown anchors
* Rejecting candidates returned for the wrong scene
* Rejecting candidates with invalid confidence
* Rejecting unsupported candidate fields
* Rejecting whitespace in machine-token fields
* Rejecting invalid candidate model construction
* Rejecting duplicate or mismatched scene evidence anchors
* Rejecting duplicate candidate identities within one scene result at the model boundary
* Normalizing human-readable candidate text without changing source quotes
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
* A candidate payload has missing or unsupported fields.
* A candidate uses whitespace in IDs, attributes, entity types, or relationship labels.
* Scene input anchor IDs and full evidence anchors do not match.
* Scene input repeats an evidence anchor.
* A candidate is treated as canonical truth.
* A candidate references a scene that was not imported.
* An extractor returns results for a different scene than the one requested.
* An extractor repeats the same entity, fact, relationship, or state-change candidate.
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

Confidence must be numeric, not boolean, and must stay between 0.0 and 1.0.

Candidate payloads must use only the supported schema fields.

Machine-token fields must be whitespace-free:

* Entity IDs
* Fact IDs
* Entity types
* Fact attributes
* Relationship types
* Source and target entity IDs
* Evidence anchor IDs

Human-readable values may contain spaces.

Human-readable candidate text is whitespace-normalized before Canon Updating sees it.

Imported scene text and evidence quotes remain source-faithful.

Scene input anchor IDs and full evidence anchor objects must match exactly.

Within one scene result, candidate identities must be unique.

Unsupported claims are omitted.

Unknown information remains Unknown.

## Core Rule

AI may propose.

Canon decides.
