# Aevryn Static Security Scan

> Built by **Aetherra Labs**

The static security scan is a Phase 11 release gate.

Core rule:

```text
Security-sensitive mistakes should be caught before runtime.
```

---

# Python Security Scan

Command:

```powershell
$env:PYTHONIOENCODING='utf-8'; python -m bandit -r src -q
```

Expected result:

```text
No findings.
```

Bandit scans the Python source tree for security-sensitive patterns such as unsafe XML parsing, shell execution, unsafe URL opening, and hardcoded risky calls.

Approved suppressions must be:

* narrow
* tied to a specific Bandit rule ID
* paired with code that enforces the safety boundary

Current accepted suppressions:

* `B310` on the OpenAI HTTPS transport after endpoint scheme validation.
* `B404`, `B603`, and `B607` on the repository secret scanner's fixed `git ls-files` command, with `shell=False`.

---

# Backend Static Checks

Commands:

```powershell
ruff check .
mypy src
```

Expected result:

```text
All checks passed!
Success: no issues found in 78 source files
```

These checks are not a substitute for Bandit, but they harden the same release surface by catching unsafe drift, typing gaps, and lint regressions before runtime.

---

# Frontend Static Checks

Commands:

```powershell
npm.cmd run lint
npm.cmd run build
```

Run from:

```text
web/
```

Expected result:

```text
eslint exits successfully.
TypeScript and Vite production build complete successfully.
```

Use `npm.cmd` on Windows when PowerShell blocks the `npm.ps1` wrapper.

---

# Security Hardening From This Gate

The Phase 11 static scan hardened Aevryn by:

* replacing standard-library XML parsing for imported documents with `defusedxml`
* requiring HTTPS endpoints before the OpenAI transport opens a request
* keeping repository secret scanning limited to a fixed `git ls-files` command with no shell
* adding strict type stubs for `defusedxml`

---

# Residual Risk

This gate does not replace:

* dynamic application security testing
* penetration testing
* code review
* browser security testing
* production infrastructure scanning
* supply-chain or container scanning

Public beta should keep this local gate and add CI enforcement before untrusted manuscript intake.
