# Aevryn Security Disclosure

> Responsible disclosure process for security researchers.

This document must be finalized before public launch.

---

# Reporting Vulnerabilities

Security researchers should report suspected vulnerabilities privately to Aetherra Labs.

Target security contact:

```text
security@aevryn.ai
```

This alias is provisioned and tested for inbound receipt, outbound product-domain sending, SPF, DKIM, DMARC, and MFA-protected operator access.

Public contact information must be published accurately before launch.

Public security contact readiness is tracked in `docs/AEVRYN_PUBLIC_SUPPORT_READINESS.md`.

Reports should include:

* affected component
* reproduction steps
* impact
* screenshots or logs without user story content
* suggested remediation if available

---

# Safe Harbor Intent

Aetherra Labs intends to work with researchers acting in good faith.

Researchers must avoid:

* accessing another user's data
* altering or deleting data
* exfiltrating secrets
* degrading service availability
* social engineering
* physical attacks
* public disclosure before remediation coordination

---

# Scope

Initial scope should include:

* Aevryn web application
* Aevryn API
* authentication and authorization boundaries
* import and upload handling
* project deletion
* monitoring and logging privacy boundaries

Final public scope must be published before launch.

---

# Response Process

Aetherra Labs should:

* acknowledge reports
* triage severity
* reproduce the issue
* fix or mitigate confirmed vulnerabilities
* communicate remediation status
* credit researchers where appropriate and permitted

No vulnerability report should require researchers to include private user manuscripts.
