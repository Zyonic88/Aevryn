# Aevryn Privacy Policy

> Draft for attorney review before public launch.

This draft describes the intended privacy posture for Aevryn. It is not a
substitute for legal review and is not approved for public beta.

---

# Scope

This draft applies to Aevryn accounts, projects, imports, generated Canon,
exports, support requests, public trust pages, and related hosted services
operated by Aetherra Labs.

---

# Information Collected

Aevryn may collect:

* account information such as email address, display name, authentication
  provider identifiers, and account settings
* authentication/session metadata used to log users in and protect accounts
* project metadata such as project names, story names, import names, run status,
  timestamps, and ownership references
* uploaded source files, pasted source text, imported story text, and source
  metadata
* generated Canon, character sheets, world sheets, timelines, scene sheets,
  prompt packs, snapshots, and exports
* usage, workflow, diagnostic, security, and audit metadata
* support, privacy, security, abuse, and legal communications

---

# How Aevryn Uses Information

Aevryn uses information to:

* create and secure accounts
* inspect, import, process, display, and export user projects
* generate evidence-backed Canon and production outputs for the user's project
* monitor workflow health and diagnose failures
* provide metadata-first support
* prevent abuse, fraud, spam, platform attacks, and unauthorized access
* comply with law and enforce platform rules
* perform backup, restore, audit, and security operations

---

# User Ownership And AI Training

Uploaded stories, pasted story text, imported source files, generated Canon,
exports, and user project data belong to the user or the rights holder they
represent.

Aetherra Labs does not train models on uploaded, pasted, imported, or generated
user story/project content by default.

Any future use of user story/project content for model training, product
improvement datasets, evaluation sharing, or donated project corpora must be
explicit, opt-in, and disclosed before collection or use.

---

# Uploaded, Pasted, And Imported Content

Aevryn uses uploaded files, pasted text, and imported story text to inspect,
process, display, organize, validate, and export project data for the user.

Aevryn should not ask users to provide full manuscripts in support requests by
default. Support should start with metadata such as project IDs, timestamps,
workflow states, screenshots with story text redacted, and concise summaries.

---

# Cookies And Local Browser Storage

Aevryn may use cookies, browser storage, or managed identity provider storage to
support login, session recovery, security, and user experience.

Before public launch, Aetherra Labs must publish the actual cookie and browser
storage posture, including purpose, duration, and user controls where required.

Current V2 alpha session behavior is bearer-session based.

---

# Analytics And Monitoring

Analytics and monitoring must be privacy-preserving.

Analytics, logs, and monitoring must not contain full source prose, full AI
payloads, credentials, tokens, local file paths, private URLs, hostnames,
usernames, serialized exports, or full manuscripts.

Hosted observability evidence confirms the current production-like posture is
metadata-only. Public launch must preserve that boundary.

---

# Authentication

Aevryn uses authentication data to create accounts, log users in, maintain
sessions, recover sessions, and protect project access.

Password hashes, bearer tokens, refresh tokens, session tokens, API keys, and
private credentials must be protected and must not be logged or displayed in
normal product surfaces.

---

# Third-Party Processors

Before public beta, Aevryn must disclose third-party processors that may receive
user data.

Current production/public-beta candidate processors include:

* Supabase for managed identity and PostgreSQL database services
* Cloudflare for DNS, R2 object storage, Pages hosting, routing, and email
  routing/sending
* Google Cloud Run and related Google Cloud services for API hosting, secrets,
  logs, and deployment operations
* OpenAI as the current provider candidate for evidence-bounded AI extraction
  when provider-backed extraction is enabled
* GitHub for source control, CI, security scanning, and operational development
  workflows

This list must be reviewed and finalized before public beta. Payment, analytics,
support, email, or additional AI providers must be added before use.

---

# AI Provider Disclosure

When provider-backed extraction is enabled, Aevryn may send selected story
excerpts, scene context, evidence anchors, extraction instructions, and
structured-output requirements to a reviewed AI provider.

The current AI provider disclosure candidate is tracked in
`docs/AEVRYN_AI_PROVIDER_DISCLOSURE_DECISION.md`. Owner product-truth provider
wording approval is recorded in
`docs/AEVRYN_PROVIDER_DISCLOSURE_WORDING_APPROVAL_2026_08_02.md`.

Current posture:

* OpenAI is the current provider candidate for evidence-bounded extraction.
* Provider output is not Canon and must be validated against story evidence
  before acceptance.
* Aevryn-side extraction requests set `store=false`.
* Owner verified API input/output sharing and evaluation/fine-tuning sharing are
  disabled for the production OpenAI project.
* Modified Abuse Monitoring, Zero Data Retention, and data residency controls
  are not represented as enabled.
* Provider-backed extraction must remain disabled for public beta until
  legal-sensitive provider wording and final public-beta signoff are complete.

---

# Data Retention

Active project and story deletion removes active Aevryn-owned product storage
for the deleted scope.

Encrypted production backups may retain deleted project or story data for up to
30 days for authorized disaster recovery only.

Current production verification:

* Supabase production plan: Pro
* Supabase daily database backup retention: 7 days
* Cloudflare R2 deletion behavior: direct delete
* R2 lifecycle expiration for deleted project/story content: not applicable

Backups are not used for AI training, analytics, support browsing, product
exploration, or employee curiosity.

Audit, security, abuse-prevention, billing, legal, and operational metadata may
have separate retention periods where necessary and disclosed.

Detailed retention principles are tracked in `docs/DATA_RETENTION_POLICY.md`.

---

# User Rights And Requests

Users may contact Aetherra Labs to request access, export, correction, deletion,
or other privacy-related handling of their account or project data.

Privacy requests should be sent to:

```text
privacy@aevryn.ai
```

Before public launch, attorney review must confirm:

* which privacy rights apply by jurisdiction
* how Aevryn verifies request identity
* response timelines
* extension timelines
* appeals process
* authorized-agent process
* exceptions for security, abuse, fraud, legal, billing, audit, and backup
  retention

Draft operating target:

* acknowledge privacy requests promptly
* verify the requester before disclosing, exporting, modifying, or deleting data
* respond within legally required timelines
* provide a review or appeal path where required by law
* record metadata-only evidence of request handling

This draft intentionally does not claim final statutory compliance until counsel
reviews jurisdiction-specific language.

---

# Sensitive Data

Aevryn is designed for creative story projects, not for processing highly
sensitive personal information.

Users should not upload government identifiers, payment card data, health
records, financial account credentials, private keys, passwords, or other
highly sensitive personal data unless Aevryn explicitly supports that data type
and publishes reviewed controls.

Attorney review must decide whether Aevryn needs consent, opt-out, or special
handling language for sensitive data under applicable law.

---

# Children's Privacy

Aevryn is not intended for children unless and until Aetherra Labs publishes an
attorney-reviewed children's privacy posture.

Before public launch, counsel must approve minimum age, parental consent,
minor-user, school-use, and content-safety language.

---

# International Users And Data Residency

Aevryn may use providers and infrastructure located in the United States or
other regions selected by Aetherra Labs.

Data residency controls are not represented as enabled for the current public
beta candidate.

Attorney review must confirm any international transfer, regional hosting, and
jurisdiction-specific disclosures before public launch.

---

# Security

Aevryn uses layered security controls including managed identity, authorization,
private object storage, metadata-only logging, audit records, restricted runtime
database access, and hosted secret management.

No system can guarantee perfect security. Users should report suspected privacy
or security issues through the contact paths below.

---

# Contact Information

Privacy contact:

```text
privacy@aevryn.ai
```

Security contact:

```text
security@aevryn.ai
```

Abuse, rights, spam, malware, and illegal-use reports:

```text
abuse@aevryn.ai
```

General support:

```text
support@aevryn.ai
```

These aliases are provisioned and tested for inbound receipt, outbound
product-domain sending, SPF, DKIM, DMARC, and MFA-protected operator access.

Public contact information must be published accurately before public launch.
