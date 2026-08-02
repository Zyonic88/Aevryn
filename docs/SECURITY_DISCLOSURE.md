# Aevryn Security Disclosure

> Draft for attorney review before public launch.

This document describes Aetherra Labs' intended responsible disclosure process
for Aevryn security researchers. It is not a substitute for legal review and is
not approved for public beta.

Responsible disclosure helps Aetherra Labs fix vulnerabilities before they can
harm Aevryn users or expose private creative work.

---

# Reporting Vulnerabilities

Security researchers should report suspected vulnerabilities privately to
Aetherra Labs.

Target security contact:

```text
security@aevryn.ai
```

This alias is provisioned and tested for inbound receipt, outbound
product-domain sending, SPF, DKIM, DMARC, and MFA-protected operator access.

Reports should include:

* affected component
* reproduction steps
* impact
* affected account or project IDs only when needed and owned by the researcher
* screenshots or logs with story text, tokens, credentials, and private data
  redacted
* suggested remediation if available

No vulnerability report should require researchers to include private user
manuscripts, full source chapters, bearer tokens, refresh tokens, API keys,
database URLs, R2 credentials, private storage references, or private signed
URLs.

---

# Initial In-Scope Systems

Initial public-beta scope should include:

* `app.aevryn.ai`
* `api.aevryn.ai`
* Aevryn account authentication and session handling
* authorization boundaries between users and projects
* import and upload handling
* project/story deletion behavior
* export access and download authorization
* monitoring and logging privacy boundaries
* security-sensitive public trust, privacy, support, and disclosure pages

Final public scope must be reviewed and published before public launch.

---

# Out Of Scope Unless Approved

The following are out of scope unless Aetherra Labs gives written permission:

* denial-of-service testing
* load testing
* spam testing
* social engineering
* phishing
* physical attacks
* attacks against employees, contractors, users, vendors, or provider support
  teams
* testing third-party providers outside Aevryn-controlled configuration
* vulnerability scans that degrade availability or trigger provider abuse
  controls
* accessing, modifying, deleting, exfiltrating, or disclosing another user's
  data

---

# Researcher Rules

Researchers must:

* use only accounts and projects they own or have explicit permission to test
* stop testing and report immediately if they encounter another user's data
* avoid persistence, lateral movement, privilege escalation beyond what is
  necessary to demonstrate impact safely, or secret extraction
* avoid public disclosure until remediation coordination is complete
* provide enough detail for Aetherra Labs to reproduce and fix the issue
* avoid submitting full manuscripts, full provider prompts/responses, or private
  user content in reports

---

# Safe Harbor Draft

Aetherra Labs intends to work with researchers acting in good faith under this
policy.

If a researcher follows this policy, Aetherra Labs intends not to pursue legal
action solely for the good-faith security research described in the report.

This safe-harbor section is a draft. Counsel must review and approve final
safe-harbor, non-retaliation, authorization, researcher privacy, and disclosure
language before public launch.

This draft does not authorize activity that violates law, harms users, accesses
another user's data, exfiltrates secrets, degrades service availability, or
targets systems outside the published scope.

---

# Response Targets

Draft operating targets:

* acknowledge receipt within 5 business days
* triage severity within 10 business days when enough information is provided
* provide status updates for confirmed high-impact reports when practical
* remediate or mitigate based on severity, exploitability, user risk, and
  engineering complexity
* credit researchers where appropriate and permitted

These are operational targets, not final legal service-level commitments.
Attorney review must approve final timelines and any disclosure commitments
before public launch.

---

# Coordinated Disclosure

Researchers should not publicly disclose a vulnerability before Aetherra Labs
has had a reasonable opportunity to investigate, mitigate, and coordinate
disclosure.

Final public disclosure timing, researcher credit, publication process, and
exceptions must be reviewed by counsel before public launch.

---

# Severity And Prioritization

Aetherra Labs should prioritize reports that could affect:

* cross-user project access
* account takeover
* unauthorized export or source-file access
* deletion bypass
* private storage references
* secrets or tokens
* metadata-only logging boundaries
* provider payload exposure
* payment or billing systems once payments exist

Low-risk issues such as missing best-practice headers, rate-limit edge cases, or
user-interface-only concerns may be handled on a longer timeline.

---

# Researcher Privacy

Aetherra Labs should use reporter contact information only to receive, triage,
coordinate, remediate, and document vulnerability reports unless another use is
required by law or approved by the researcher.

Final researcher privacy language must be reviewed by counsel before public
launch.

---

# Abuse Reports Are Different

Security vulnerability reports should go to:

```text
security@aevryn.ai
```

Platform abuse, spam, malware, illegal-use, copyright, or rights reports should
go to:

```text
abuse@aevryn.ai
```
