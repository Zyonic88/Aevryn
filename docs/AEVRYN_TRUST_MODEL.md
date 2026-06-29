# Aevryn Trust Model

> Built by **Aetherra Labs**

Why should someone trust Aevryn?

Because Aevryn is designed around a simple principle:

```text
Your work belongs to you.
```

---

# Evidence-Backed Canon

Aevryn treats the uploaded story as the source of truth.

Canon facts must be backed by evidence anchors. If Aevryn cannot support a claim from the story, the correct answer is uncertainty, not invention.

---

# Deterministic Outputs

Aevryn separates source import, extraction, canon acceptance, presentation, and export.

That separation makes outputs easier to inspect, test, rebuild, and challenge.

---

# User Ownership

Users own:

* uploaded stories
* generated canon
* generated exports
* production prompt packs
* future user-generated assets

Aetherra Labs does not claim ownership of user manuscripts or generated continuity data.

---

# Transparency

Aevryn should explain:

* what was imported
* what was extracted
* what evidence supports a fact
* what changed over time
* what failed and why
* what data is available for export or deletion

Opaque magic is not trust.

---

# Privacy

Story content is private by default.

Aevryn must not log full source prose, full AI responses, credentials, tokens, local paths, hostnames, usernames, or serialized exports in diagnostics.

---

# Security

Security is architecture, not a feature.

Aevryn protects users through authentication, authorization, fail-closed production configuration, metadata-only monitoring, audit logging, repository secret scanning, dependency auditing, static security scanning, and deletion boundaries.

---

# Architecture

The platform is layered:

```text
Website
-> API
-> Engine
-> Storage
```

The frontend does not invent backend truth.

The API does not expose source prose where metadata is enough.

The engine remains evidence-bound.

---

# AI Never Owns Truth

AI can propose.

Canon must be accepted through evidence.

If AI output conflicts with the story, the story wins.

If AI output lacks evidence, it does not become truth.
