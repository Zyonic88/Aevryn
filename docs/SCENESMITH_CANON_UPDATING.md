# SceneSmith Canon Updating

## What Is It?

Canon Updating is the gate between extraction candidates and canonical truth.

Extraction may propose.

Canon Updating validates.

Canon Database stores.

## Why Does It Exist?

AI output is not truth.

SceneSmith needs a controlled process that asks:

* Evidence?
* Confidence?
* Current Canon?
* Version Update?

Only then can Canon change.

## What Authority Does It Own?

Canon Updating owns:

* Candidate validation
* Evidence anchor conversion into Evidence records
* Scene-to-evidence consistency checks
* Confidence threshold enforcement
* New entity creation from accepted candidates
* Fact creation from accepted candidates
* Relationship creation from accepted candidates
* Version update decisions

It owns the decision to submit accepted changes to Canon Database.

## V1 Rules

Relationship candidates may connect entities accepted in the same scene or already stored in Canon.

The extractor does not have to restate both relationship endpoint entities in every scene.

Evidence anchors supplied to one Canon update must be unique.

Minimum confidence must be numeric, not boolean, and bounded from 0.0 to 1.0.

Duplicate semantic relationships are idempotent and must not be reported as newly accepted.

Accepted state-change summary IDs must refer to stored Canon Database state-change records.

Explicit state-change candidates validate the accepted fact state; they must not create phantom summary IDs.

Canon update summaries must not classify the same candidate ID as both accepted and rejected.

## What Does It NOT Own?

Canon Updating does not own:

* AI extraction
* Source import structure
* Canon storage internals
* Character card assembly
* Scene context
* Prompt generation
* Export formatting

It does not invent missing evidence.

## How Does It Fail?

Canon Updating can fail if:

* A candidate has no evidence anchor.
* A candidate confidence is below threshold.
* A candidate references an unknown source anchor.
* The extraction result scene does not match the supplied evidence anchors.
* The supplied evidence anchors contain duplicate anchor IDs.
* A relationship references entities that were not accepted or already stored.
* Existing canon is overwritten instead of versioned.
* AI candidates are treated as truth before validation.

Rejected candidates must not change Canon.

## How Does It Interact With Other Systems?

Story Import provides evidence anchors.

Entity Extraction provides candidates.

Canon Updating validates candidates against evidence anchors and confidence.

Canon Database stores accepted entities, facts, relationships, and state changes.

Character, Scene, Prompt, and Export systems consume accepted Canon only.
