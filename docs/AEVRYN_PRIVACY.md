# Aevryn Privacy

> Built by **Aetherra Labs**

Aevryn exists to understand stories, not to own them.

Privacy is a product promise and an architecture requirement.

---

# Privacy Philosophy

```text
Your stories are yours.
Aevryn is built to understand them, not to own them.
```

Uploaded manuscripts, imported chapters, canon snapshots, generated output views, and exports belong to the creator.

Aetherra Labs must never rely on hidden ownership claims, hidden training rights, or unclear retention behavior.

---

# Creator Ownership

Aevryn's privacy posture:

* User stories belong to the user.
* Canon built from those stories belongs to the user.
* Generated exports belong to the user.
* Aetherra Labs does not claim ownership of uploaded manuscripts.
* Aetherra Labs does not claim ownership of generated continuity data.
* Aetherra Labs does not train models on user stories without explicit opt-in.

---

# Story Privacy

Story files are high-trust data.

They may include:

* unpublished novels
* screenplays
* comic scripts
* private worldbuilding notes
* proprietary franchise material
* commissioned creative work

Aevryn must treat story content as private by default.

Default expectations:

* no full source prose in logs
* no full source prose in monitoring
* no full source prose in performance artifacts
* no full AI payloads in logs
* no hidden story copies after deletion
* no training use without explicit opt-in
* no support access without explicit user permission

---

# Data Minimization

Phase 11 should ask this for every persisted field:

```text
Do we need this data?
For how long?
Who can access it?
How is it deleted?
```

Required minimization rules:

* store metadata when metadata is enough
* avoid storing source prose in operational artifacts
* bound diagnostics to concise summaries
* avoid retaining failed upload payloads
* avoid logging tokens, credentials, local paths, usernames, hostnames, or raw provider responses

---

# Deletion Promise

Deletion must be real.

When a user deletes a story, Aevryn must remove:

* story metadata
* saved import metadata
* stored source bytes
* engine runs scoped to that story
* snapshots scoped to that story
* exports scoped to that story
* derived output records scoped to that story
* queued or completed background job metadata scoped to that story

Deletion must not create a new hidden manuscript copy in an audit log, monitoring event, error payload, or support artifact.

Backup retention behavior is defined in `docs/AEVRYN_BACKUP_RETENTION.md`.

If production backups retain deleted data for a bounded recovery window, that window must be explicit and disclosed.

---

# Export And Portability

Privacy includes user control.

Phase 11 should define future requirements for:

* project export
* story export
* generated output export
* account data export
* deletion receipts or deletion status

These do not need to become broad new product features during Phase 11, but the privacy contract should describe the direction before public beta.

---

# Account Deletion

Account deletion is a future product surface, but the privacy rule is already fixed:

```text
Deleting an account must remove or anonymize Aevryn-owned active user data unless retention is legally or operationally required and disclosed.
```

Account deletion must cover user profile data, projects, stories, imports, snapshots, exports, session state, and associated active product metadata.

---

# Third-Party AI Providers

Provider-backed extraction is opt-in through configuration.

Aevryn must disclose before public beta:

* which providers can receive story content
* what content is sent
* whether providers retain input or output
* whether providers train on submitted content
* how provider failures are logged without source prose

Aevryn must not silently route manuscripts to third parties.

---

# Data Residency

Public beta must define where production data is stored and processed.

Until production regions are selected, Aevryn must not promise a specific data residency region.

---

# Internal Employee Access

Employees and contractors must not browse customer stories by default.

Access to uploaded stories, generated canon, exports, backups, and account data must be:

* limited by role
* justified by support, security, or recovery need
* logged where technically possible
* reviewed for abuse
* never used for training or curiosity access

---

# AI Data Use

Default rule:

```text
Never train on user stories by default.
```

Any future training contribution must be:

* opt-in
* explicit
* separate from normal product use
* transparent about what is shared
* reversible where technically possible
* unavailable for minors or restricted users if required by law or policy

Anonymization alone is not enough to make hidden training acceptable.

---

# Public Trust Language

Future website and product copy should be able to say:

```text
Your stories are yours.
Aevryn never claims ownership of your manuscripts.
Aevryn never trains on your projects without explicit opt-in.
Deleted stories are removed from Aevryn-owned active storage.
```

Those statements must remain true in the architecture before they appear in public marketing.

---

# Out Of Scope

This privacy document does not create:

* legal terms of service
* a production privacy policy
* compliance certification
* public launch readiness

It defines the engineering promise Phase 11 must make technically true.
