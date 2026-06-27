# Aevryn Logging Policy

> Built by **Aetherra Labs**

This document defines the V1 logging contract for aevryn.

Logging exists to make system behavior observable without mixing operational details into user-facing output.

---

# Rule

Core systems use module-level loggers.

CLI commands may use `print` only for user-facing command output and expected error messages.

The package root installs a `NullHandler` so library logs do not leak unless the host application configures logging.

No core subsystem should use `print`.

---

# Logger Standard

Every implemented V1 subsystem module should define:

```python
logger = logging.getLogger(__name__)
```

Subsystems should log meaningful lifecycle events, validation outcomes, rejected inputs, or generated output summaries.

Subsystems should not log full source chapters, private story text, or full AI responses.

---

# Levels

Use `debug` for deterministic internal summaries.

Use `info` for completed workflow steps.

Use `warning` for recoverable rejected inputs or conflicts.

Use exceptions for invalid state and programmer errors.

---

# Boundaries

Logging must not change behavior.

Logging must not become presentation.

Logging must not replace structured return values.

Logging must not expose copyrighted source text beyond short evidence quotes already preserved by Canon.

---

# V1 Contract

The logging policy is V1 ready when:

* Core subsystem modules use module-level loggers.
* Package logging is quiet by default.
* User-facing CLI output remains separate from operational logging.
* No core subsystem uses `print`.
* Tests verify the logging boundary.
