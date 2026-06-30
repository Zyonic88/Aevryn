# Aevryn Alias Provisioning Record

> Built by **Aetherra Labs**

Use this record while provisioning the `aevryn.ai` public contact aliases.

This document should be filled in after the aliases are created and tested.

---

# Status

```text
Record: Public Contact Alias Provisioning
Status: Not provisioned
Public beta: Blocked
```

Public beta remains blocked until the required aliases are provisioned, secured, tested, and published.

---

# Provider

Email provider:

```text
TBD
```

DNS provider:

```text
TBD
```

Mailbox or forwarding model:

```text
TBD - mailbox, group, alias, routing rule, or helpdesk inbox.
```

Admin owner:

```text
TBD
```

MFA enabled for admin access:

```text
TBD
```

---

# Required Aliases

| Alias | Purpose | Recipient/Owner | Provisioned | Inbound Tested | Reply Tested | MFA/Access Reviewed |
| --- | --- | --- | --- | --- | --- | --- |
| `support@aevryn.ai` | Product support, account access, import/export help, project deletion help | TBD | No | No | No | No |
| `privacy@aevryn.ai` | Privacy questions, account deletion, backup retention, AI provider data-use questions | TBD | No | No | No | No |
| `security@aevryn.ai` | Vulnerability reports, account compromise, suspected data exposure | TBD | No | No | No | No |
| `abuse@aevryn.ai` | Platform abuse, spam, malware, illegal use reports, rights escalation | TBD | No | No | No | No |

Optional future aliases:

| Alias | Purpose | Status |
| --- | --- | --- |
| `legal@aevryn.ai` | Counsel/legal routing | Future |
| `billing@aevryn.ai` | Billing support if payments exist | Future |

---

# DNS And Deliverability

Record DNS/mail settings after setup:

| Setting | Required Result | Actual Result |
| --- | --- | --- |
| MX records | Point to selected provider | TBD |
| SPF | Present and provider-aligned | TBD |
| DKIM | Enabled if provider supports it | TBD |
| DMARC | Present before public beta | TBD |
| Test inbound delivery | Each alias receives mail | TBD |
| Test outbound replies | Replies send from expected identity | TBD |

If only inbound forwarding is available at first, reply identity must still be reviewed before publishing the alias publicly.

---

# Test Messages

For each alias, send a synthetic test message that contains no real manuscript content.

Recommended subject format:

```text
Aevryn alias test - <alias> - YYYY-MM-DD
```

Record:

| Alias | Sent From | Received By | Reply Sent | Result | Notes |
| --- | --- | --- | --- | --- | --- |
| `support@aevryn.ai` | TBD | TBD | TBD | TBD | TBD |
| `privacy@aevryn.ai` | TBD | TBD | TBD | TBD | TBD |
| `security@aevryn.ai` | TBD | TBD | TBD | TBD | TBD |
| `abuse@aevryn.ai` | TBD | TBD | TBD | TBD | TBD |

---

# Triage Expectations

Initial target triage:

| Alias | Initial Target |
| --- | --- |
| `support@aevryn.ai` | Acknowledge within 2 business days during beta |
| `privacy@aevryn.ai` | Acknowledge within 2 business days during beta |
| `security@aevryn.ai` | Acknowledge vulnerability reports as soon as practical |
| `abuse@aevryn.ai` | Acknowledge urgent platform-abuse reports as soon as practical |

These are operational targets, not legal service-level agreements.

---

# Redaction Guidance

Public support instructions must tell users not to send:

* full manuscripts
* full chapters
* full AI responses
* generated exports unless explicitly requested
* passwords
* API keys
* provider keys
* session tokens
* private URLs
* screenshots containing private story text
* machine-local paths

Support may ask for:

* account email or user identifier
* project name or project ID
* short issue summary
* error code
* approximate time of issue
* redacted screenshots

---

# Publication Checklist

Before public beta, add verified contact aliases to:

* Privacy Policy
* Security Disclosure
* support page
* trust page
* public website footer or contact page
* release-candidate run record

Do not publish untested aliases.

---

# Acceptance

Alias provisioning is accepted when:

```text
The required aevryn.ai aliases are provisioned, secured, tested for inbound and reply behavior, and published with clear private-story redaction guidance.
```
