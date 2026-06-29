# Aevryn Repository Secret Scan

> Built by **Aetherra Labs**

The repository secret scan is a Phase 11 release gate.

Core rule:

```text
Release files must not contain credentials.
```

---

# Scope

The scanner checks git-tracked repository files by default.

It intentionally does not scan ignored local development files such as:

* `.env.aevryn.local`
* local caches
* temporary files
* machine-specific runtime output

That keeps the gate focused on what could be committed, reviewed, packaged, or pushed.

If a local secret file becomes tracked, it enters scan scope automatically.

---

# Covered Secret Shapes

The Phase 11 scanner detects:

* OpenAI-style API keys
* AWS access-key IDs
* private-key block headers
* generic hardcoded key, secret, token, and password assignments

Findings are reported with:

* file path
* line number
* stable rule ID
* redacted snippet

The scanner must not print the secret value it finds.

---

# Allowed Placeholders

Documentation and tests may include obvious placeholders.

Allowed examples include:

* `AEVRYN_OPENAI_API_KEY=...`
* `secret-provider-key`
* local development placeholders
* test-only credentials clearly marked as fake/test/sample/redacted

Placeholders must remain visibly non-production.

---

# Command

From the repository root:

```powershell
$env:PYTHONPATH='src'; python -m aevryn.security.secret_scan
```

Expected result:

```text
Repository secret scan passed: <n> files scanned.
```

---

# Residual Risk

This gate does not replace:

* production secret management
* cloud secret scanning
* GitHub push protection
* dependency auditing
* static security scanning
* manual review of deployment configuration

Public beta should use this local scanner plus hosted repository secret scanning and protected branch checks.
