# Aevryn V2 Phase 11 Acceptance

> Built by **Aetherra Labs**

Phase 11 makes Aevryn trustworthy enough to approach public beta.

Core rule:

```text
Security is architecture.
Privacy is product integrity.
```

Phase 11 starts after private internal alpha has exposed the product path and before Aevryn accepts untrusted public users.

---

# Required Contract

Phase 11 starts with:

* `docs/AEVRYN_SECURITY.md`
* `docs/AEVRYN_PRIVACY.md`
* `docs/AEVRYN_API_SECURITY_HARDENING.md`
* `docs/AEVRYN_AUDIT_LEDGER.md`
* this acceptance document
* `docs/AEVRYN_PHASE_11_SECURITY_GATES.md`
* explicit authorization-boundary audit
* explicit deletion-boundary audit
* explicit no-source-prose logging audit
* production security posture decisions
* repeatable security verification gates

---

# Acceptance Criteria

Phase 11 is accepted when:

* Security architecture is documented.
* Privacy architecture is documented.
* Security is treated as an architectural gate before public beta.
* Identity hardening is reviewed and documented.
* Authorization boundary tests cover cross-user project, story, import, run, snapshot, export, settings, and deletion access.
* Story privacy principles are documented and reflected in API/logging behavior.
* Deleting a story removes story metadata, imports, source bytes, runs, snapshots, and exports scoped to that story.
* Deletion behavior is tested at metadata and source-storage boundaries.
* Backup retention behavior is documented before public beta.
* No full chapter text is logged.
* No full manuscript text is logged.
* No full AI response is logged.
* No credentials, tokens, password hashes, API keys, machine-local paths, hostnames, or usernames are logged in diagnostics.
* Upload validation and request-size limits are documented and tested.
* CORS policy is documented and tested.
* Security headers are documented and tested for production deployment.
* Rate limiting strategy is documented, even if final infrastructure implementation waits for deployment.
* Production security configuration fails closed when required secrets or policies are missing.
* Secrets management is documented.
* Dependency auditing is part of the release gate.
* Repository secret scanning is part of the release gate.
* Static security scanning is part of the release gate.
* Audit ledger architecture is documented.
* Audit records are metadata-only and never preserve deleted source prose.
* AI privacy defaults are documented: no training on user stories without explicit opt-in.
* Frontend displays security/privacy states provided by the API where backend state matters.
* Frontend does not invent authorization, deletion, or security state.
* Backend gates pass.
* Frontend gates pass.
* Aevryn validation passes.

---

# Security Verification Gates

Phase 11 should produce repeatable gates:

* Authentication Regression Test
* Authorization Boundary Test
* Deletion Integrity Test
* Privacy Logging Test
* Upload Validation Test
* API Hardening Test
* Audit Ledger Integrity Test
* Dependency Audit
* Repository Secret Scan
* Static Security Scan
* Production Configuration Fail-Closed Test

Each gate should record:

* command or procedure
* expected result
* latest result
* known residual risk
* whether public beta is blocked

---

# Audit Ledger Acceptance

The audit ledger is accepted only when:

* records are append-only
* records are hash chained or otherwise tamper evident
* records contain stable event types
* records contain stable actor/project/story references where appropriate
* records contain concise summaries only
* records contain no source prose
* records contain no full AI responses
* integrity verification is automated
* deletion events do not preserve deleted content

---

# Privacy Acceptance

Privacy is accepted only when the product can truthfully say:

```text
Uploaded stories belong to the creator.
Generated canon belongs to the creator.
Generated exports belong to the creator.
Aetherra Labs does not claim ownership of user manuscripts.
Aetherra Labs does not train on user stories without explicit opt-in.
Deleted stories are removed from Aevryn-owned active storage.
```

If any of those statements is not technically true, Phase 11 is not complete.

---

# Out Of Scope

Phase 11 does not include:

* new creator workflow features
* public launch
* payments implementation
* team collaboration
* publishing
* image generation
* video generation
* chatbot behavior
* broad frontend redesign
* marketing copy that exceeds the verified security/privacy contract

Phase 11 may define future requirements for account deletion, project export, user-data export, enterprise audit views, and compliance posture, but it should not become a broad product expansion phase.
