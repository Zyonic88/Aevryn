# Aevryn Public Trust Page Copy

> Built by **Aetherra Labs**

This document drafts the plain-language public trust pages for `aevryn.ai`.

It is copy-ready only where marked.

Legal-sensitive sections still require attorney review before public beta.

---

# Copy Rules

Public trust copy must be:

* plain-language
* true to current architecture
* clear about public-beta blockers
* careful around backups, providers, deletion, and employee access
* free of internal-only terms such as phase numbers, release gates, local adapters, and implementation gates

Public copy must not imply Aevryn is public-beta approved before signoff.

---

# Trust Page

Readiness:

```text
Draft-ready. Final publication still depends on public-beta signoff.
```

Draft copy:

```text
Your work belongs to you.

Aevryn is built to understand stories, not to own them.

When you upload a manuscript, chapter, screenplay, comic script, or worldbuilding note, you keep ownership of your work. Aetherra Labs does not claim ownership of your uploaded stories, generated canon, continuity data, prompt packs, or exports.

Aevryn treats your story as the source of truth. Canon facts must be backed by evidence from the story. If Aevryn cannot support a claim from the source, the right answer is uncertainty, not invention.

AI can help propose structure. AI does not own truth. Your story wins.
```

---

# Privacy Page

Readiness:

```text
Draft only. Attorney review, provider disclosure, and production retention windows required. Privacy contact is verified.
```

Draft copy:

```text
Your stories are private by default.

Aevryn uses uploaded stories to inspect, import, process, display, and export project data for your account.

Aetherra Labs does not train on user stories without explicit opt-in.

Aevryn is designed to avoid putting full manuscripts, full chapters, full AI responses, credentials, tokens, private URLs, or machine-local paths into logs, monitoring, diagnostics, or support workflows.

When you delete a story, Aevryn removes it from active Aevryn-owned product storage. The current public-beta wording candidate says encrypted production backups may retain deleted project or story data for up to 30 days for authorized disaster recovery only. Backups are not used for AI training, analytics, support browsing, or product exploration.

When provider-backed extraction is enabled, Aevryn may send selected story excerpts, scene context, evidence anchors, extraction instructions, and structured-output requirements to a reviewed AI provider. The current provider candidate is OpenAI. Provider output is not Canon; Aevryn validates provider output against story evidence before accepting anything into project state. Provider-backed extraction must remain disabled for public beta unless provider data-use terms, retention behavior, abuse-monitoring behavior, and no-training posture are reviewed, documented, and disclosed accurately.

Privacy questions should go to privacy@aevryn.ai.
```

---

# Security Page

Readiness:

```text
Draft only. Production monitoring, incident response, branch protection, and public-page publication required. Security contact is verified.
```

Draft copy:

```text
Security is architecture, not a feature.

Aevryn protects user projects through authentication, authorization, private storage boundaries, metadata-only monitoring, security scanning, dependency review, and fail-closed production configuration.

The website does not grant authority by itself. Backend authorization decides which projects, stories, imports, snapshots, and exports an account can access.

Uploaded manuscripts and generated exports must remain private. Aevryn is designed so diagnostics and support workflows can investigate problems without asking for full source prose by default.

Security vulnerability reports should go to security@aevryn.ai.
```

---

# User Rights Page

Readiness:

```text
Draft-ready. Backup and deletion wording must be aligned with final production retention windows.
```

Draft copy:

```text
Your story: you own it.

Your canon: you own it.

Your exports: you own them.

Aevryn is a tool for understanding your work. It is not a claim over your work.

You should be able to export your data and delete your projects. Deleted stories are removed from active Aevryn-owned product storage. The current public-beta wording candidate says encrypted backups may retain deleted project or story data for up to 30 days for authorized disaster recovery only.

AI training is off by default. Aetherra Labs does not train on user stories without explicit opt-in.

Employees do not browse customer stories by default. Access must be limited, justified, and auditable where technically possible.
```

---

# Content Classification Page

Readiness:

```text
Draft-ready. Legal and provider-policy review required before public beta.
```

Draft copy:

```text
Aevryn is content-aware, not content-opinionated.

Creators work across many genres, audiences, and formats. Aevryn may classify projects as General, Teen, Mature, or Explicit so the product can handle visibility, provider restrictions, exports, and future moderation responsibly.

Lawful mature fiction is not automatically prohibited.

Content classification does not change ownership. Your stories remain yours.
```

---

# Support Page

Readiness:

```text
Draft-ready for contact details. Legal-sensitive publication and support procedure review still required.
```

Draft copy:

```text
Need help with Aevryn?

Use support@aevryn.ai for product support, account access help, import or processing issues, export issues, and project deletion help.

Use privacy@aevryn.ai for privacy questions, account deletion requests, backup retention questions, or AI provider data-use questions.

Use security@aevryn.ai for vulnerability reports, suspected account compromise, or suspected data exposure.

Use abuse@aevryn.ai for platform abuse, spam, malware, illegal use reports, copyright or rights escalations, or attempts to access another user's data.

Please do not send full manuscripts, full chapters, full AI responses, passwords, API keys, provider keys, session tokens, private URLs, screenshots containing private story text, or machine-local paths.

Helpful reports usually include your account email, project name or project ID, a short issue summary, an error code if shown, approximate time of the issue, and redacted screenshots.
```

---

# Security Disclosure Page

Readiness:

```text
Draft only. Attorney safe-harbor review and security mailbox verification required.
```

Draft copy:

```text
Aetherra Labs welcomes good-faith security reports for Aevryn.

Please report suspected vulnerabilities privately to security@aevryn.ai.

Reports should include the affected component, reproduction steps, impact, screenshots or logs without private story content, and suggested remediation if available.

Please avoid accessing another user's data, altering or deleting data, exfiltrating secrets, degrading service availability, social engineering, physical attacks, or public disclosure before remediation coordination.

No vulnerability report should require private user manuscripts.
```

---

# Publication Blockers

Before these pages can be published for public beta:

* verified contact aliases must be published accurately
* legal-sensitive pages must be attorney-reviewed
* production backup retention window must be verified against the selected public-beta wording candidate
* AI provider review must be completed against the selected disclosure candidate or provider-backed extraction must remain disabled
* production security operations must be configured
* claims must be checked against the final public-beta deployment

---

# Acceptance

Public trust copy is accepted when:

```text
The public pages explain Aevryn's trust promises in plain language without overpromising public-beta readiness, deletion behavior, provider behavior, employee access, or backup behavior.
```
