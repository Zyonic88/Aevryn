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
* race
* gender
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

When source text explicitly states character identity facts such as gender, race, species, role, profession, family context, relationship context, appearance, equipment, abilities, assets, goals, limitations, or status, extraction should capture them as evidence-backed facts with stable attributes. Gendered kinship/title terms such as sister, brother, mother, father, wife, husband, princess, or prince count as explicit gender evidence only for the character being described. Race/species labels such as Half-Beastman count as explicit race/species evidence only for the character being described. It should not infer gender or race from names alone, another character, a group merely being discussed, or a chapter title/question. Gendered group phrases such as female soldiers or male recruits describe that group, not a separate named character.

Machine IDs are allowed as secondary metadata, but they should not be the main reading experience.

---

# Worker Extraction Source

The worker depends on the existing `SceneExtractor` boundary.

Default local alpha mode uses the deterministic proof extractor.

Configured alpha AI mode may inject an evidence-bounded extractor behind that worker boundary.

The worker still follows the same authority chain:

```text
SceneExtractor
-> Extraction candidates
-> Canon Updating
-> Canon snapshot
-> Presentation panels
```

That means provider-backed AI can propose candidates without writing directly to Canon, persistence, logs, or frontend state.

Aevryn now has an OpenAI Responses API `AIExtractionClient` adapter behind the same protocol. It is not the default worker path.

Provider-backed extraction must be explicitly configured before any story text is sent to an external model.

Environment wiring supports:

* `AEVRYN_EXTRACTION_MODE=demo`
* `AEVRYN_EXTRACTION_MODE=openai`

OpenAI mode requires `AEVRYN_OPENAI_API_KEY` and `AEVRYN_OPENAI_MODEL`.

Provider-backed extraction requests schema-constrained JSON and then still passes the result through Aevryn's evidence-bounded validator before Canon Updating.

Repeatable local provider smoke:

```text
aevryn provider-smoke --env-file .env.aevryn.local
```

The provider smoke uses synthetic text only and prints metadata counts only.

The remaining alpha limitation is live provider validation. Broad story understanding should stay disabled for testers until provider behavior, cost, latency, privacy language, and failure states are verified.
