# Aevryn API Security Hardening

> Built by **Aetherra Labs**

This document defines the Phase 11 API hardening contract for the V2 platform API.

Core rule:

```text
The API fails closed before public beta.
```

API hardening protects the boundary where browsers, workers, storage, and future provider-backed extraction meet user manuscripts.

---

# Current Enforced Controls

## Stable Error Shapes

API errors return stable machine-readable codes through the shared error response contract.

Required behavior:

* malformed requests return `invalid_request`
* malformed base64 returns `invalid_base64`
* oversized source uploads return `import_content_too_large`
* missing workflow API keys return `authentication_required`
* invalid workflow API keys return `invalid_api_key`
* missing project storage returns `project_storage_unavailable`
* cross-user project access fails closed with not-found style errors

## Request IDs

Every response carries `X-Request-ID`.

Valid caller-provided request IDs are echoed for trace correlation.

Whitespace-bearing request IDs are rejected and replaced with generated IDs.

## Workflow Route Protection

When API keys are configured, workflow routes require:

* `X-Aevryn-API-Key`
* or `Authorization: Bearer <key>`

Discovery routes remain public metadata routes.

Duplicate API keys are rejected at app creation.

## Upload And Request-Size Boundary

Import source content is limited to 10 MiB decoded bytes per request.

Oversized source payloads fail before parsing or storage.

This is an API boundary. Production deployments must also configure request-body limits at the proxy/server layer.

## CORS And Browser Security Headers

CORS is disabled by default.

Configured CORS origins must be explicit.

Wildcard CORS is rejected.

Every API response includes browser-facing security headers:

* `X-Content-Type-Options: nosniff`
* `X-Frame-Options: DENY`
* `Referrer-Policy: no-referrer`
* `Permissions-Policy: camera=(), microphone=(), geolocation=()`

## Production Fail-Closed Configuration

When `AEVRYN_DEPLOYMENT_ENV=production`, the app refuses to start unless these are present:

* `AEVRYN_PROJECT_DATABASE_ADAPTER=postgresql`
* `AEVRYN_PROJECT_DATABASE_URL`
* `AEVRYN_API_ALLOWED_ORIGINS`
* `AEVRYN_API_KEYS`
* `AEVRYN_IMPORT_STORAGE_ADAPTER=object`
* `AEVRYN_IMPORT_STORAGE_BUCKET`
* `AEVRYN_IMPORT_STORAGE_ENDPOINT_URL`
* `AEVRYN_IMPORT_STORAGE_ACCESS_KEY_ID`
* `AEVRYN_IMPORT_STORAGE_SECRET_ACCESS_KEY`
* `AEVRYN_IMPORT_STORAGE_PREFIX`

This prevents accidental public startup with stateless storage, local source-byte storage, missing Cloudflare R2 storage credentials, missing browser-origin policy, or unprotected workflow routes.

Production mode rejects `AEVRYN_PROJECT_DATABASE_PATH` because local JSON Project Database storage is not allowed for public deployment.
Production mode rejects `AEVRYN_IMPORT_STORAGE_PATH` because local filesystem source-byte storage is not allowed for public deployment.

---

# Rate Limiting Strategy

Phase 11 documents rate limiting as a production gate, but final infrastructure-specific enforcement belongs to deployment architecture.

Public beta should apply rate limits at the edge or API gateway, with at least these buckets:

* authentication attempts
* password reset requests
* import inspection and import creation
* worker submission and retry routes
* provider-backed extraction routes
* export preview routes

Rate-limit responses should use a stable machine-readable error code such as `rate_limited` and must not include source prose, full AI payloads, credentials, tokens, hostnames, usernames, or machine-local paths.

Local development does not enforce production rate limits yet.

Public beta remains blocked until the deployment layer defines and tests concrete thresholds.

---

# CSRF Posture

The V2 alpha API uses bearer-session authorization headers.

Browser cookies are not the current session authority.

If cookies become the browser session authority later, Aevryn must add CSRF protection before public beta. That future CSRF layer should include:

* SameSite cookie policy
* secure cookies
* CSRF token or equivalent double-submit protection
* mutation-route coverage
* tests proving cross-site form requests cannot mutate user data

Until then, frontend route hiding is convenience only. Backend authentication and authorization remain the source of truth.

---

# Timeout Policy

Provider-backed extraction must keep explicit timeout and response-size limits.

Current provider settings:

* `AEVRYN_OPENAI_TIMEOUT_SECONDS`
* `AEVRYN_OPENAI_MAX_RESPONSE_BYTES`

Invalid timeout and response-size configuration fails at app creation.

Public beta must define deployment-level request timeout behavior for:

* upload requests
* worker submission
* provider-backed extraction
* export preview
* health and monitoring reads

Timeout errors must use stable machine-readable codes and must not log source prose or full provider responses.

---

# Public Beta Blockers

API hardening does not unblock public beta until:

* production rate limits are configured and tested
* production request-body limits are configured and tested
* HTTPS/HSTS behavior is defined at the deployment edge
* cookie/CSRF posture is finalized if cookies are introduced
* provider timeout and retention behavior are documented
* API security checks are included in the release gate
