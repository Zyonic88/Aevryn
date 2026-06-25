# SceneSmith Web Import System

## What Is It?

The Web Import System imports story source references from the web in a respectful, permission-aware way.

It begins with a URL.

It does not begin with scraping.

Its job is to determine whether SceneSmith can import from a web source, collect source metadata, discover chapter links when allowed, and preserve attribution for evidence references.

For V1, manual upload and pasted chapters remain the primary import path.

Web Import is powerful, but it adds legal, technical, and anti-scraping complexity.

## Why Does It Exist?

Creators often work with stories hosted online.

SceneSmith eventually needs a safe way to help users import those sources without violating site rules, bypassing access restrictions, or republishing copyrighted text.

The Web Import System exists so URL-based intake has one clear authority boundary instead of being mixed into Story Import, Canon, or Extraction.

## What Authority Does It Own?

The Web Import System owns:

* URL intake
* Source metadata extraction
* Chapter discovery
* Source attribution
* Import permission checks
* Robots.txt checks
* Rate-limit policy for web fetching
* Login and paywall boundary detection
* User confirmation before import

The ideal flow is:

```text
Paste URL
-> Check import permissions
-> Pull metadata and chapter list
-> User confirms import
-> Fetch chapters slowly and respectfully
-> Hand source text to Story Import
-> Store evidence references, not republished chapters
```

## What Does It NOT Own?

The Web Import System does not own:

* Canon truth
* AI extraction
* Copyright bypass
* Paywall bypass
* Login bypass
* Prompt generation
* Character cards
* Scene reconstruction
* Export formatting
* Republishing source chapters

It never presents scraped copyrighted text as SceneSmith-owned content.

It never treats accessible text as permission to redistribute that text.

## How Does It Fail?

The Web Import System can fail if:

* The site disallows crawling or automated access.
* Robots.txt blocks the target path.
* The source requires login.
* The source is behind a paywall.
* The site rate-limits requests.
* Chapter discovery is ambiguous.
* Metadata is missing or inconsistent.
* The source changes during import.
* The URL points to user-generated content with unclear permissions.
* The system stores full copyrighted chapters as generated output.
* The system strips attribution from imported evidence.

When permission is unclear, Web Import should stop and ask the user to use manual upload or paste instead.

It should fail closed.

## How Does It Interact With Other Systems?

Web Import sends approved source text and source attribution into Story Import.

Story Import owns chapter parsing, scene splitting, paragraph indexing, sentence indexing, and evidence anchors.

Entity Extraction may later read the imported scenes, but it does not decide whether the web source was allowed.

Canon Updating may accept facts extracted from web-imported text only when those facts include valid evidence anchors.

The Canon Engine stores evidence references and accepted truth.

The Export Engine may include source attribution and evidence references, but it must not republish source chapters as SceneSmith-owned content.

The Project Manager may coordinate Web Import as one intake option.

## V1 Boundary

For V1, SceneSmith should prioritize:

* Manual upload
* Pasted chapters
* Local files

Web Import should begin as a documented system and later start with conservative support:

* URL validation
* Metadata preview
* Chapter list preview
* Permission checks
* User confirmation

Full automated fetching should wait until the permission model is tested and clearly documented.

## Core Rules

Respect site terms, robots.txt, login rules, paywall rules, and rate limits.

Never bypass access controls.

Never present scraped copyrighted text as SceneSmith-owned content.

Store evidence references and attribution.

Prefer manual upload or paste when web permissions are unclear.
