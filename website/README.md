# Aevryn Public Website

> Built by **Aetherra Labs**

This folder contains the static public website intended for `https://aevryn.ai`.

The production application remains separate at:

```text
https://app.aevryn.ai
```

## Boundary

The public website may explain Aevryn, link to the hosted app, and publish approved public trust/support copy.

The public website must not:

* imply public beta is approved before final signoff
* publish legal-sensitive language as final before attorney review
* collect manuscripts, chapters, passwords, API keys, tokens, or private URLs
* implement product workflows that belong to the Aevryn app/API
* duplicate engine, Canon, import, processing, export, or account logic

## Deployment

Deploy this folder as a static Cloudflare Pages site for `aevryn.ai`.

Recommended Cloudflare Pages settings:

```text
Root directory: website
Build command: none
Build output directory: .
Production branch: master
```

## Source

This repo-owned version fixes encoding issues, removes fake form behavior, and keeps public-beta wording conservative until legal review and final signoff are complete.
