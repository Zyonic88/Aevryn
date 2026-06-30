# Aevryn Alias Provisioning Record

> Built by **Aetherra Labs**

Use this record while provisioning the `aevryn.ai` public contact aliases.

This document should be filled in after the aliases are created and tested.

---

# Status

```text
Record: Public Contact Alias Provisioning
Status: Inbound, DNS, and access verified; reply review pending
Public beta: Blocked
```

Public beta remains blocked until the required aliases are provisioned, secured, tested, and published.

---

# Provider

Email provider:

```text
Cloudflare Email Routing
```

DNS provider:

```text
Cloudflare
```

Mailbox or forwarding model:

```text
Cloudflare Email Routing aliases forwarding to aetherra.project@gmail.com.
```

Admin owner:

```text
Aetherra Labs
```

MFA enabled for admin access:

```text
Verified. Cloudflare MFA and Gmail MFA are enabled.
```

---

# Required Aliases

| Alias | Purpose | Recipient/Owner | Provisioned | Inbound Tested | Reply Tested | MFA/Access Reviewed |
| --- | --- | --- | --- | --- | --- | --- |
| `support@aevryn.ai` | Product support, account access, import/export help, project deletion help | `aetherra.project@gmail.com` | Yes | Yes | No | Yes |
| `privacy@aevryn.ai` | Privacy questions, account deletion, backup retention, AI provider data-use questions | `aetherra.project@gmail.com` | Yes | Yes | No | Yes |
| `security@aevryn.ai` | Vulnerability reports, account compromise, suspected data exposure | `aetherra.project@gmail.com` | Yes | Yes | No | Yes |
| `abuse@aevryn.ai` | Platform abuse, spam, malware, illegal use reports, rights escalation | `aetherra.project@gmail.com` | Yes | Yes | No | Yes |

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
| Test inbound delivery | Each alias receives mail | Passed. All four aliases delivered to `aetherra.project@gmail.com`. |
| Cloudflare routing health | Email Routing status and DNS records enabled | Passed. Cloudflare shows Status Enabled, DNS records Enabled, 4 routing rules, 1 destination, 9 received, 9 forwarded, 0 failed, and 0 rejected. |
| Test outbound replies | Replies send from expected identity | TBD |
| Admin/account MFA | Cloudflare and destination mailbox MFA enabled | Passed. Cloudflare MFA and Gmail MFA are enabled. |

Cloudflare Email Routing verifies inbound receiving and forwarding. Outbound SPF, DKIM, DMARC, and branded reply posture remain tied to the final reply-identity decision.

If only inbound forwarding is available at first, reply identity must still be reviewed before publishing the alias publicly.

Outbound reply identity setup is tracked in `docs/AEVRYN_REPLY_IDENTITY_SETUP.md`.

---

# Reply Identity Policy

Product-specific Aevryn correspondence should reply from the matching `aevryn.ai` product identity.

Expected reply identities:

| Mail Type | Reply Identity |
| --- | --- |
| Aevryn support, privacy, security, abuse, deletion, account, import, export, or story-processing issues | Product-specific `aevryn.ai` alias |
| Aevryn product announcements sent by Aetherra Labs | Aetherra Labs or a product-specific `aevryn.ai` sender, depending on message context |
| Aetherra Labs company, legal, press, hiring, or multi-product communication | Aetherra Labs sender |
| Aetherra product-specific communication | Aetherra product sender |

Core rule:

```text
Replies should come from the specific product identity unless Aetherra Labs is intentionally speaking as the company.
```

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
| `support@aevryn.ai` | `zyonic88@gmail.com` | `aetherra.project@gmail.com` | TBD | Passed inbound | Gmail filter routes to Aevryn support folder. |
| `privacy@aevryn.ai` | `zyonic88@gmail.com` | `aetherra.project@gmail.com` | TBD | Passed inbound | Gmail filter routes to Aevryn privacy folder. |
| `security@aevryn.ai` | `zyonic88@gmail.com` | `aetherra.project@gmail.com` | TBD | Passed inbound | Gmail filter routes to Aevryn security folder. |
| `abuse@aevryn.ai` | `zyonic88@gmail.com` | `aetherra.project@gmail.com` | TBD | Passed inbound | Gmail filter routes to Aevryn abuse folder. |

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

Do not publish an alias as a support contact until both inbound receipt and outbound reply identity have been tested, unless the public page clearly says the address is intake-only.

---

# Current Progress

```text
Cloudflare Email Routing rules are created for support, privacy, security, and abuse aliases.
All four aliases currently route to aetherra.project@gmail.com.
Inbound delivery from zyonic88@gmail.com to all four aliases passed.
Gmail filters route all four Aevryn aliases into their respective folders.
Cloudflare MFA and Gmail MFA are enabled.
Cloudflare Email Routing health passed for inbound routing: Status Enabled, DNS records Enabled, 9 received, 9 forwarded, 0 failed, 0 rejected.
Reply identity remains open with Cloudflare Email Sending selected as the preferred provider candidate.
Outbound-specific SPF, DKIM, and DMARC posture remains tied to Cloudflare Email Sending configuration and reply testing.
Outbound reply identity setup is tracked in docs/AEVRYN_REPLY_IDENTITY_SETUP.md.
```

---

# Acceptance

Alias provisioning is accepted when:

```text
The required aevryn.ai aliases are provisioned, secured, tested for inbound and reply behavior, and published with clear private-story redaction guidance.
```
