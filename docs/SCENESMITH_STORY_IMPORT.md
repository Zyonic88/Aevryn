# SceneSmith Story Import

## What Is It?

Story Import is the system that turns source story text into stable, addressable source structure.

It does not analyze meaning.

It does not extract characters.

It does not decide canon.

It creates the source map that evidence depends on.

AI may later read this structure, but AI does not own the source structure or the truth derived from it.

## Why Does It Exist?

Evidence needs anchors.

SceneSmith cannot reliably say:

```text
Chapter 12
Scene 4
Paragraph 18
Sentence 3
```

unless Story Import owns the structure of the imported story.

Without Story Import, evidence becomes vague and difficult to verify.

Story Import exists so every future fact can point back to a stable location in the source material.

## What Authority Does It Own?

Story Import owns:

* Source document intake
* Chapter parsing
* Scene splitting
* Paragraph indexing
* Sentence indexing
* Source references
* Chapter IDs
* Scene IDs
* Evidence anchors
* Source order preservation

Supported inputs:

* TXT
* EPUB
* PDF
* DOCX
* Markdown
* Copied chapters

## What Does It NOT Own?

Story Import does not own:

* Canon facts
* Character extraction
* Relationship extraction
* Timeline state changes
* Prompt generation
* Image generation
* Export formatting
* User accounts
* Payments

It prepares source structure.

It does not interpret story meaning.

## How Does It Fail?

Story Import can fail if:

* Chapter order is lost.
* Scene boundaries are unstable.
* Paragraph indexes change unexpectedly.
* Sentence indexes cannot be traced back to source text.
* Evidence anchors point to the wrong source location.
* It silently guesses structure when the source is ambiguous.
* It mutates imported text without preserving the original.

When structure is ambiguous, Story Import should preserve the ambiguity instead of pretending certainty.

## How Does It Interact With Other Systems?

Story Import provides stable source references to later analysis and extraction work.

The Canon Engine uses evidence anchors when recording facts.

AI extraction systems may propose facts from Story Import anchors, but Canon decides what becomes truth.

The Timeline Engine uses chapter and scene ordering from Story Import.

The Character Engine benefits from evidence-backed character facts created from imported source structure.

The Scene Engine relies on stable scene IDs and scene positions.

The Export Engine can include source references in external sheets.

## Evidence Anchor Shape

An evidence anchor should eventually be able to identify:

```text
Source
Chapter
Scene
Paragraph
Sentence
Character offset
```

This allows SceneSmith to prove where a fact came from.
