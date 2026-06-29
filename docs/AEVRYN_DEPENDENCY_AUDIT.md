# Aevryn Dependency Audit

> Built by **Aetherra Labs**

The dependency audit is a Phase 11 release gate.

Core rule:

```text
Release dependencies must be known and auditable.
```

---

# Dependency Surfaces

Aevryn has two dependency surfaces in Version 2:

* Python backend and engine dependencies in `pyproject.toml`
* Web frontend dependencies in `web/package-lock.json`

Both surfaces must pass vulnerability auditing before public beta.

---

# Python Audit

Command:

```powershell
python -m pip_audit . --progress-spinner off
```

Expected result:

```text
No known vulnerabilities found
```

This command audits the local Aevryn project dependency set.

Do not use a raw environment audit as the release signal. A developer machine may contain unrelated global packages that are not Aevryn dependencies.

If a Python lockfile is introduced later, the Phase 11 gate should move to a locked dependency audit.

---

# Frontend Audit

Command:

```powershell
npm audit --audit-level=high
```

Run from:

```text
web/
```

Expected result:

```text
found 0 vulnerabilities
```

The frontend audit is backed by `web/package-lock.json`.

---

# Dependency Policy

Before public beta:

* production dependencies must be reviewed intentionally
* lockfiles must be committed where the ecosystem supports them
* vulnerability audits must run before release
* high or critical vulnerabilities must block release unless explicitly documented and accepted
* dependency updates must not weaken authentication, authorization, deletion, logging, or privacy behavior

---

# Residual Risk

This gate does not replace:

* Dependabot or equivalent hosted dependency alerts
* protected branch checks
* software bill of materials generation
* license review
* transitive dependency ownership review
* production container/image scanning

Public beta should use this local audit plus hosted dependency monitoring and CI enforcement.
