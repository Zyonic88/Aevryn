# Aevryn Story Import

## What Is It?

Story Import is the system that turns source story text into stable, addressable source structure.

It does not analyze meaning.

It does not extract characters.

It does not decide canon.

It creates the source map that evidence depends on.

AI may later read this structure, but AI does not own the source structure or the truth derived from it.

## Why Does It Exist?

Evidence needs anchors.

Aevryn cannot reliably say:

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
* Source-map integrity
* Source order preservation
* Explicit chapter order validation
* File-format adapters that prepare readable text for Story Import

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

## Native Source Format Support

V1.1 supported:

* TXT
* Markdown
* HTML/XHTML
* FB2
* DOCX
* ODT
* EPUB
* Copied chapters

Deferred:

* PDF
* MOBI
* AZW3

Rule:

Never claim source-format support until the parser is deterministic, tested,
and preserves evidence-anchor integrity.

The current support table is maintained in `docs/AEVRYN_IMPORT_FORMAT_MATRIX.md`.

Compiled and structured file support is adapter-based.

Adapters extract deterministic readable text, remove navigation-only material
where applicable, normalize text, and pass that text to the existing Story
Import parser.

They must not become separate story parsers.

## How Does It Fail?

Story Import can fail if:

* Chapter order is lost.
* Explicit multi-chapter headings move backward or duplicate a chapter index.
* Scene boundaries are unstable.
* Paragraph indexes change unexpectedly.
* Sentence indexes cannot be traced back to source text.
* Evidence anchors point to the wrong source location.
* It silently guesses structure when the source is ambiguous.
* It mutates imported text without preserving the original.
* EPUB metadata is malformed.
* EPUB spine documents cannot be found or decoded.
* EPUB navigation or table-of-contents material leaks into imported story text.
* DOCX, ODT, or FB2 XML is malformed.
* PDF, MOBI, or AZW3 is supplied before parser support is enabled.

When structure is ambiguous, Story Import should preserve the ambiguity instead of pretending certainty.

A standalone chapter file may preserve its explicit heading index, such as Chapter 2.

A multi-chapter source must keep explicit chapter headings in increasing order.

Imported source structures must be internally consistent:

* Imported source IDs must match the story ID.
* Paragraphs must reference known scene IDs.
* Sentences must reference their owning paragraph.
* Sentence text must be traceable to the owning paragraph text.
* Paragraph IDs, sentence IDs, and anchor IDs must be unique.
* Paragraph indexes must be unique inside each scene.
* Evidence anchors must reference known paragraphs and sentences.
* Evidence anchors must reference known chapters and scenes.
* Evidence anchor scenes must belong to their referenced chapters.
* Evidence anchor scenes must match their paragraph scenes.
* Evidence anchor sentences must belong to their referenced paragraphs.
* Evidence anchor paragraph indexes must match their referenced paragraphs.
* Evidence anchor sentence indexes must match their referenced sentences.
* Evidence anchor quotes must exactly match their referenced sentence text.
* Evidence anchors must belong to the imported source.

## How Does It Interact With Other Systems?

Story Import provides stable source references to later analysis and extraction work.

File adapters provide clean text to Story Import. Story Import still owns
chapter parsing, scene splitting, paragraph indexing, sentence indexing, and
evidence anchors.

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

This allows Aevryn to prove where a fact came from.
