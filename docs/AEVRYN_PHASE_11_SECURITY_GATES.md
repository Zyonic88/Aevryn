# Aevryn Phase 11 Security Gates

> Built by **Aetherra Labs**

Phase 11 security gates are repeatable checks for public-beta trust readiness.

Core rule:

```text
Security is architecture.
Privacy is product integrity.
```

Each gate records the command or procedure, expected result, latest result, known residual risk, and whether public beta is blocked.

---

# Gate 1 - Authentication Regression Test

Command:

```text
python -m pytest tests/test_auth_api.py -q
```

Expected result:

* registration, login, session, password reset, project ownership, import, run, snapshot, monitoring, output, and deletion auth tests pass.
* auth failures use stable machine-readable errors.
* no test response exposes credentials, tokens beyond explicit session contract fields, source prose, full AI payloads, serialized export content, storage references, machine-local paths, hostnames, or usernames.

Latest result:

```text
38 passed
```

Known residual risk:

* production identity provider, cookie policy, account lockout, and deployment secret requirements still need explicit Phase 11 review.

Public beta blocked:

```text
Yes
```

---

# Gate 2 - Authorization Boundary Test

Command:

```text
python -m pytest tests/test_auth_api.py::test_phase11_project_surfaces_fail_closed_across_users -q
```

Expected result:

* cross-user project, settings, story, import, run, snapshot, status/export metadata, output, and deletion requests fail closed.
* failed cross-user responses do not leak source prose, export IDs, serialized export content, or storage references.

Latest result:

```text
1 passed
```

Known residual risk:

* future routes must be added to this boundary test before they can be considered public-beta ready.
* frontend route hiding is convenience only; backend authorization remains the source of truth.

Public beta blocked:

```text
Yes
```

---

# Gate 3 - Deletion Integrity Test

Command:

```text
python -m pytest tests/test_auth_api.py::test_delete_story_api_hard_deletes_metadata_and_import_content -q
```

Expected result:

* deleting a story removes story metadata, import metadata, stored source bytes, engine runs, snapshots, and export metadata scoped to that story.
* post-delete status reports no snapshot or export availability for the deleted story data.
* deletion does not leave source bytes readable through Aevryn-owned import storage.

Latest result:

```text
1 passed
```

Known residual risk:

* production backup retention behavior is not yet documented.
* production object-storage deletion semantics are not yet defined.
* deletion receipts and account-level deletion remain future privacy work.

Public beta blocked:

```text
Yes
```

---

# Gate 4 - Privacy Logging Test

Command:

```text
python -m pytest tests/test_auth_api.py::test_phase11_privacy_logging_gate_excludes_private_story_payloads -q
```

Expected result:

* API, worker, and persistence workflow logs do not preserve source prose.
* logs do not preserve full AI-response-shaped text, credentials, tokens, source payload bytes, machine-local paths, or hostnames.
* logs do not expose serialized snapshot output as a hidden copy of processed story data.

Latest result:

```text
1 passed
```

Known residual risk:

* this gate currently covers the storage-backed product path; standalone CLI logging and future provider integrations must be included before public beta.
* production log aggregation, retention, and access controls are not yet documented.

Public beta blocked:

```text
Yes
```

---

# Remaining Gates

The following gates still need Phase 11 implementation before public beta:

* Upload Validation Test
* API Hardening Test
* CORS And Security Header Test
* Audit Ledger Integrity Test
* Dependency Audit
* Repository Secret Scan
* Static Security Scan
* Production Configuration Fail-Closed Test
