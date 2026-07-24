# Aevryn Export Engine

## What Is It?

The Export Engine converts Aevryn data into external formats.

It outputs:

* JSON
* Markdown
* CSV
* Character Sheets
* Scene Sheets
* World Sheets
* Prompt Sheets
* Production Packs

It does not own the data it exports.

## Why Does It Exist?

Creators need to move Aevryn context into other tools.

The Export Engine exists so Canon, Timeline, Character, Scene, and Prompt outputs can be used outside Aevryn without changing the underlying state.

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

JSON output preserves Unicode text instead of ASCII-escaping repaired names, titles, or dialogue.

JSON output preserves machine-readable detail for audits, tests, and downstream tools.

CSV output uses stable headers.

CSV output must reject duplicate headers, missing row fields, and unexpected row fields.

Markdown output remains human-readable and does not mix unrelated formats.

Markdown output is presentation-first and optimized for creator scanning.

Markdown list rows are whitespace-normalized before deduplication.

Repeated Markdown list items are deduplicated.

Markdown list output must reject blank visible rows.

Continuity Report JSON exports preserve the full audit trail.

Continuity Report Markdown exports summarize retained canon and raw state-change records so humans can scan what changed without losing access to machine-readable evidence.

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
* It silently emits CSV rows that do not match the configured header schema.
* It corrupts or ASCII-escapes Unicode text that creators need to read.
* It drops snapshot identifiers needed to trace exported scene context.
* It drops evidence context needed to audit continuity changes.
* It exposes raw validity-event internals in human Markdown reports instead of summarizing them.
* It emits blank Markdown list rows.

Unknown information should remain absent or represented as Unknown.

## How Does It Interact With Other Systems?

The Character Engine provides character cards.

The Scene Engine provides scene context.

The Prompt Engine provides prompt bundles.

The Export Engine serializes those objects into external formats.

Future file-writing behavior should be handled explicitly and separately.

## V2 Beta Stored Export Limits

The V2 beta stored-export surface is intentionally narrow.

Supported stored export:

* Latest accepted Canon snapshot
* JSON format
* Authenticated project-owner download
* Private object storage behind the API

The frontend may display export metadata such as filename, format, size,
checksum, and creation time. It must not display storage references, bucket
paths, private object URLs, credentials, or serialized export bytes in the
stored-export list.

Developer export previews may still show explicit preview content behind a
collapsed disclosure control because the user deliberately requested a preview.
Stored exports are different: they are downloaded through the authenticated API
boundary and are not rendered into the workspace by default.

Not included in the V2 beta stored-export surface unless explicitly re-scoped:

* batch exports
* production-pack file generation
* character-sheet file generation
* prompt-bundle file generation
* generated media assets
* public or shared export links
* signed URL handoff to the frontend

The public beta acceptance target is that users can create and download the
allowed Canon Snapshot JSON export without exposing private storage references
or crossing project-owner authorization boundaries.
