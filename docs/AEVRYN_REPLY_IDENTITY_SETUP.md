# Aevryn Reply Identity Setup

> Built by **Aetherra Labs**

This document tracks the outbound reply identity Aevryn needs before public beta.

Inbound aliases are already routed through Cloudflare Email Routing. That proves Aevryn can receive mail.

It does not, by itself, prove that Aevryn can send trusted replies from product-domain addresses.

---

# Status

```text
Gate: Product reply identity
Status: Started
Public beta: Blocked
```

Public beta remains blocked until replies can be sent from the expected product identity and the result is tested.

---

# Core Rule

```text
Replies should come from the specific product identity unless Aetherra Labs is intentionally speaking as the company.
```

Aevryn support should feel like Aevryn.

Aetherra Labs should be used when the company is intentionally speaking as the operator, legal entity, or parent brand.

---

# Identity Model

| Message Type | Expected Sender |
| --- | --- |
| Aevryn support | `support@aevryn.ai` |
| Aevryn privacy | `privacy@aevryn.ai` |
| Aevryn security | `security@aevryn.ai` |
| Aevryn abuse reports | `abuse@aevryn.ai` |
| Aevryn deletion or account help | `support@aevryn.ai` or `privacy@aevryn.ai` |
| Aevryn product announcements | Aevryn product sender or Aetherra Labs, depending on message context |
| Aetherra Labs company, legal, press, hiring, or multi-product messages | Aetherra Labs sender |
| Aetherra product-specific messages | Aetherra product sender |

---

# Recommended Options

## Option A - Managed Business Mailbox

Use a hosted mailbox provider that supports custom-domain sending, SPF, DKIM, and DMARC.

Examples:

* Google Workspace
* Microsoft 365
* Fastmail
* Proton Mail business
* dedicated helpdesk mailbox provider

This is the preferred public-beta posture because the mail provider owns both receiving and sending behavior.

## Option B - Helpdesk With Verified Sending

Use a support/helpdesk provider that can send from verified `aevryn.ai` identities.

This can work well once Aevryn has enough support volume to need ticket assignment, labels, templates, and audit trails.

The helpdesk must not encourage users to upload full manuscripts by default.

## Option C - Gmail Send-As Bridge

Use the existing destination mailbox for triage while configuring verified custom-domain send-as identities through an SMTP provider.

This is acceptable only if:

* replies visibly come from the intended `aevryn.ai` alias
* SPF, DKIM, and DMARC pass
* the sender is not presented as an untrusted Gmail relay
* MFA remains enabled
* private-story redaction guidance remains visible to support operators

---

# Required DNS Posture

Before public beta, outbound mail must have:

| Setting | Requirement |
| --- | --- |
| SPF | Provider-aligned sending source is authorized |
| DKIM | Provider signs outbound mail for the sending domain |
| DMARC | Domain policy exists before public beta |
| From identity | Replies show the expected product-domain alias |
| Reply-To | Replies route back to the correct product-domain alias |
| Bounce handling | Delivery failures are visible to the operator |

Inbound Cloudflare Email Routing DNS health is already recorded in `docs/AEVRYN_ALIAS_PROVISIONING_RECORD.md`.

Outbound DNS remains separate until the reply provider is selected.

---

# Test Plan

Use synthetic test messages only.

Do not include real manuscripts, chapters, AI outputs, credentials, private URLs, or machine-local paths.

For each alias:

1. Send an inbound test to the alias.
2. Reply from the expected product identity.
3. Confirm the recipient sees the expected `From` display name and address.
4. Confirm replies route back into the correct folder or queue.
5. Confirm SPF, DKIM, and DMARC pass in received message details.
6. Record the result in `docs/AEVRYN_ALIAS_PROVISIONING_RECORD.md`.

Required reply tests:

| Alias | Required Result | Status |
| --- | --- | --- |
| `support@aevryn.ai` | Reply sends as Aevryn support identity | Not tested |
| `privacy@aevryn.ai` | Reply sends as Aevryn privacy identity | Not tested |
| `security@aevryn.ai` | Reply sends as Aevryn security identity | Not tested |
| `abuse@aevryn.ai` | Reply sends as Aevryn abuse identity | Not tested |

---

# Public-Beta Blockers

Public beta remains blocked until:

* outbound reply provider is selected
* product-domain reply identities are configured
* SPF, DKIM, and DMARC posture is verified
* all four required aliases pass reply tests
* support operators know not to request full source prose by default
* public support, privacy, security, and trust pages list only tested contact paths

---

# Acceptance

This setup is accepted when:

```text
Aevryn can receive and reply through tested product-domain identities without weakening user-story privacy or confusing product and company sender authority.
```
