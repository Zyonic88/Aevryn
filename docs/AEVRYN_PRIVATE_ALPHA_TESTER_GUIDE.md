# Aevryn Private Alpha Tester Guide

> Built by **Aetherra Labs**

This guide is for narrow private alpha testing only.

Aevryn is not public-release ready. Do not use this alpha for public users, payments, production hosting, collaboration, media generation, or untrusted manuscript intake.

---

# Purpose

Private alpha testers should answer one question:

```text
Can a creator use the V2 workspace path without touching the CLI?
```

The tested path is:

```text
Register or log in
-> Create a project
-> Create or select a story
-> Upload supported chapter files
-> Inspect and save the import
-> Submit processing
-> Wait for processing to finish
-> Review Monitoring when needed
-> Review Characters, World, Timeline, Scenes, Continuity, Prompt Packs, and Exports
```

---

# Test Rules

Use only test material you are allowed to upload.

Do not upload:

* private client work
* paid customer manuscripts
* legal, medical, financial, or confidential documents
* API keys, passwords, tokens, or credentials
* personally sensitive information

For Phase 10, prefer small batches first. The current alpha path has been exercised most heavily with 1 to 10 chapter imports.

---

# What To Test

Create a new project and story.

Upload supported native files:

* `.txt`
* `.md`
* `.markdown`
* `.html`
* `.htm`
* `.xhtml`
* `.fb2`

After import processing succeeds, review:

* Characters: character cards should be readable and should not show conflicting gender values.
* World: world entries should be readable and grouped into sheets.
* Timeline: scene-by-scene changes should be understandable and should avoid machine-noise repetition.
* Scenes: scene sheets should show imported structure and scene-level production context.
* Continuity: continuity should show accepted changes when extraction produced canon facts, or a clear waiting state when it did not.
* Prompt Packs: prompts should be useful, canon-bounded, and explicit about unknown details.
* Exports: export options should be visible without exposing full export content unless previewed.
* Monitoring: workflow state should come from the API and should help explain failures.

---

# What Counts As A Bug

Report issues when:

* the API is unreachable while the server is expected to be running
* import save loses inspected chapter data
* processing gets stuck and the user cannot continue
* old runs block new imports incorrectly
* project deletion fails or leaves the UI in a broken state
* output tabs show raw machine IDs where creator-facing text is expected
* output tabs infer details that are not in accepted canon
* errors expose source prose, full AI payloads, credentials, tokens, usernames, hostnames, or machine-local paths
* the frontend appears to infer backend workflow state instead of displaying API-provided state

Include:

* project name
* story name
* approximate chapter count
* tab where the issue appeared
* visible error message
* whether refresh or login recovery let you continue

Do not include full source prose in bug reports.

---

# Known Alpha Limitations

This alpha is local/private readiness, not production readiness.

Known limitations:

* Web Import is unavailable.
* Large imports can be slow, especially with provider-backed AI extraction.
* Production worker restart/reclaim behavior is not final.
* Production database, object storage, hosted identity, deployment, payments, teams, collaboration, and public launch are out of scope.
* AI extraction can still misclassify sparse race/gender evidence when the source is indirect.
* Local/demo extraction may show unknown canon fields. That is expected when no accepted AI facts exist.
* Prompt Packs must not invent unknown appearance, setting, item, or relationship details.
* Security & Privacy Hardening is Phase 11 and must happen before public beta.

---

# Tester Continue Criteria

After any failure, answer:

```text
Can I continue?
```

Good alpha behavior:

* refresh restores project state
* login recovery returns to a useful workspace
* Monitoring explains the current run or latest failure
* failed runs do not block unrelated future imports
* processed outputs remain visible after refresh

Bad alpha behavior:

* source data disappears after save
* a stale run blocks normal use forever
* the UI invents workflow status
* the UI exposes private source text in diagnostics
* deleting a project leaves recoverable copies in Aevryn-owned active storage

Project deletion and broader privacy guarantees will receive deeper hardening in Phase 11 before public beta.
