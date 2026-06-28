# Aevryn AI Extraction Alpha

> Built by **Aetherra Labs**

AI extraction turns imported story structure into evidence-backed canon candidates.

Core rule:

```text
AI may propose.
Canon decides.
Presentation explains.
```

Phase 10 alpha extraction must make processed story output readable without weakening the authority boundaries that already exist.

---

# Alpha Contract

The alpha workflow is:

```text
Saved import
-> Background worker
-> Evidence-bounded extraction
-> Canon Updating
-> Canon snapshot
-> Presentation panels
-> Workspace output views
```

The worker may create durable snapshot metadata from a processed import.

The worker must not expose:

* raw chapter text
* full source prose
* raw AI responses
* prompt text
* credentials
* local machine paths

The project output API may expose:

* project status metadata
* canon counts
* character profile panels
* world sheet panels
* evidence summaries
* section titles and compact fact values

The frontend renders API-provided output only.

---

# Human-Readable Output

Character output should read like a living character panel:

* identity
* status
* current goal
* equipment
* abilities
* assets
* territory
* relationships
* limitations
* recent changes
* evidence summary

World output should read like a world sheet:

* world entity name
* entity type
* known facts
* connected relationships
* evidence summary

Unknown information remains `Unknown`.

Machine IDs are allowed as secondary metadata, but they should not be the main reading experience.

---

# Current Alpha Limitation

The existing worker path uses the deterministic proof extractor unless a real evidence-bounded AI extraction source is wired in.

That means the alpha UI can prove the workflow and presentation contract before broad story understanding is enabled.

The next extraction slice should add a real extraction source behind the existing `AIExtractionClient` boundary without letting the AI write directly to Canon.
