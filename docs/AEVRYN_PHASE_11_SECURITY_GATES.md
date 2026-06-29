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

* production backup retention behavior is documented in `docs/AEVRYN_BACKUP_RETENTION.md`, but final deployment-specific retention windows are not selected yet.
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

# Gate 5 - Upload Validation Test

Command:

```text
python -m pytest tests/test_backend_api.py::test_import_inspect_endpoint_rejects_oversized_upload tests/test_auth_api.py::test_story_imports_api_rejects_oversized_uploads_before_storage -q
```

Expected result:

* stateless import inspection rejects oversized source payloads before parsing.
* authenticated story import rejects oversized source payloads before persistence.
* oversized payload failures use stable `413 import_content_too_large` responses.
* rejected story imports do not create import metadata or stored source bytes.

Latest result:

```text
2 passed
```

Known residual risk:

* final public-beta upload size may change after production storage, queue, and provider limits are selected.
* request-body limits at the deployment proxy/server layer still need production configuration.
* archive expansion limits for DOCX, ODT, EPUB, and FB2 should be reviewed before public beta.

Public beta blocked:

```text
Yes
```

---

# Gate 6 - CORS And Security Header Test

Command:

```text
python -m pytest tests/test_backend_api.py::test_cors_is_disabled_by_default tests/test_backend_api.py::test_create_app_can_enable_configured_cors_origin tests/test_backend_api.py::test_create_app_from_env_configures_cors_origins tests/test_backend_api.py::test_create_app_from_env_rejects_wildcard_cors_origin tests/test_backend_api.py::test_api_responses_include_security_headers -q
```

Expected result:

* CORS is disabled by default.
* explicit browser origins can be configured through app creation and environment settings.
* wildcard CORS origins fail closed.
* successful responses and structured error responses include browser-facing security headers.

Latest result:

```text
5 passed
```

Known residual risk:

* final production origin list must be selected during deployment.
* HTTPS-only enforcement and HSTS should be applied at the production edge once domains and TLS termination are known.
* CSP for the frontend app shell should be defined with the final asset and API domains.

Public beta blocked:

```text
Yes
```

---

# Gate 7 - Production Configuration Fail-Closed Test

Command:

```text
python -m pytest tests/test_backend_api.py::test_create_app_from_env_fails_closed_for_incomplete_production_config tests/test_backend_api.py::test_create_app_from_env_accepts_explicit_production_security_config -q
```

Expected result:

* `AEVRYN_DEPLOYMENT_ENV=production` refuses to start without explicit project storage.
* production mode refuses to start without explicit CORS origins.
* production mode refuses to start without API keys for workflow routes.
* complete production security config starts successfully and reports configured storage.

Latest result:

```text
2 passed
```

Known residual risk:

* production database, identity provider, worker queue, object storage, secret manager, HTTPS/HSTS edge policy, and observability retention choices are still deployment architecture decisions.
* API keys are a deployment boundary, not the final public-user authorization model.
* final production extraction mode and provider-retention policy still need public-beta review.

Public beta blocked:

```text
Yes
```

---

# Gate 8 - API Hardening Test

Command:

```text
python -m pytest tests/test_phase11_security.py::test_api_security_hardening_document_covers_required_controls tests/test_backend_api.py::test_import_inspect_endpoint_rejects_invalid_base64 tests/test_backend_api.py::test_import_inspect_endpoint_rejects_oversized_upload tests/test_backend_api.py::test_import_inspect_endpoint_returns_stable_validation_error tests/test_backend_api.py::test_api_echoes_client_request_id tests/test_backend_api.py::test_api_generates_request_id_when_client_value_is_invalid tests/test_backend_api.py::test_api_key_auth_rejects_missing_key_for_workflow_routes tests/test_backend_api.py::test_api_key_auth_rejects_invalid_key_for_workflow_routes tests/test_backend_api.py::test_create_app_rejects_duplicate_api_keys tests/test_backend_api.py::test_create_app_from_env_fails_closed_for_incomplete_production_config -q
```

Expected result:

* API hardening documentation covers stable errors, request IDs, workflow route protection, upload/request-size boundaries, CORS/security headers, production fail-closed config, rate limiting strategy, CSRF posture, timeout policy, and public-beta blockers.
* malformed source payloads and malformed API requests fail with stable machine-readable errors.
* oversized import payloads fail before parsing or storage.
* request IDs are echoed only when valid.
* workflow routes are protected when API keys are configured.
* duplicate API keys fail at app creation.
* incomplete production configuration fails closed.

Latest result:

```text
10 passed
```

Known residual risk:

* production rate limiting is documented but still belongs to the deployment edge or API gateway.
* production request-body limits and timeout enforcement still need deployment-layer tests.
* CSRF protection is not required while bearer headers remain the session authority, but must be added before cookie-backed sessions become authoritative.

Public beta blocked:

```text
Yes
```

---

# Gate 9 - Audit Ledger Integrity Test

Command:

```text
python -m pytest tests/test_audit_ledger.py -q
```

Expected result:

* audit records append in sequence order.
* records are hash chained and tamper evident.
* reordered or modified records fail verification.
* audit metadata rejects source text, serialized output, credentials, secrets, tokens, machine-local paths, and non-concise prose.
* deletion events can record counts and scope without preserving deleted story content.

Latest result:

```text
5 passed
```

Known residual risk:

* production audit storage adapter is not selected yet.
* audit retention and access-control policy still need deployment decisions.
* API and worker events are not fully wired into a persisted production ledger yet.

Public beta blocked:

```text
Yes
```

---

# Gate 10 - Repository Secret Scan

Command:

```text
$env:PYTHONPATH='src'; python -m aevryn.security.secret_scan
```

Expected result:

* git-tracked release files are scanned by default.
* ignored local development files, including local env files, are not scanned unless they become tracked.
* OpenAI-style keys, AWS access-key IDs, private-key blocks, and hardcoded key/secret/token/password assignments are detected.
* findings include path, line number, stable rule ID, and a redacted snippet.
* findings do not print full secret values.
* documented placeholders and test-only fake credentials do not fail the gate.

Latest result:

```text
Repository secret scan passed: 280 files scanned.
```

Known residual risk:

* hosted repository secret scanning and push protection still need to be configured before public beta.
* production secret management and cloud-provider secret storage remain deployment decisions.
* dependency auditing and static security scanning are separate remaining Phase 11 gates.

Public beta blocked:

```text
Yes
```

---

# Gate 11 - Dependency Audit

Command:

```text
python -m pip_audit . --progress-spinner off
```

Expected result:

* the local Aevryn Python project dependency set is audited.
* unrelated global developer-machine packages are not treated as the Aevryn release signal.
* known vulnerabilities in project dependencies fail the gate.

Latest result:

```text
No known vulnerabilities found
```

Command:

```text
npm audit --audit-level=high
```

Run from:

```text
web/
```

Expected result:

* frontend production and development dependencies are audited from `web/package-lock.json`.
* high or critical vulnerabilities fail the gate.

Latest result:

```text
found 0 vulnerabilities
```

Known residual risk:

* Python dependency auditing is project-scoped, not lockfile-scoped, because Aevryn does not yet have a Python lockfile.
* hosted dependency alerts and protected branch checks still need to be configured before public beta.
* SBOM generation, license review, and production image/container scanning remain future release-hardening work.

Public beta blocked:

```text
Yes
```

---

# Gate 12 - Static Security Scan

Command:

```text
$env:PYTHONIOENCODING='utf-8'; python -m bandit -r src -q
```

Expected result:

* Python source is scanned for security-sensitive static patterns.
* unsafe XML parsing, unsafe URL opening, and subprocess use are either fixed or narrowly justified.
* suppressions are tied to specific Bandit rule IDs and backed by code-level safety checks.

Latest result:

```text
No findings.
```

Command:

```text
ruff check .
mypy src
```

Expected result:

* backend lint and strict typing checks pass.

Latest result:

```text
All checks passed!
Success: no issues found in 78 source files
```

Command:

```text
npm.cmd run lint
npm.cmd run build
```

Run from:

```text
web/
```

Expected result:

* frontend lint passes.
* TypeScript and Vite production build complete successfully.

Latest result:

```text
eslint exited successfully.
Vite production build completed successfully.
```

Known residual risk:

* local static scanning does not replace CI enforcement, code review, DAST, penetration testing, or production infrastructure scanning.
* accepted suppressions must be reviewed again before public beta.
* production container/image scanning remains future release-hardening work.

Public beta blocked:

```text
Yes
```

---

# Remaining Gates

The following gates still need Phase 11 implementation before public beta:

```text
None.
```
