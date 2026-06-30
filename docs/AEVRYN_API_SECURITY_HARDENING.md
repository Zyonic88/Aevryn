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
* `AEVRYN_PUBLIC_FRONTEND_BASE_URL`
* `AEVRYN_PUBLIC_API_BASE_URL`
* `AEVRYN_HTTPS_ONLY=true`
* `AEVRYN_HSTS_ENABLED=true`
* `AEVRYN_API_KEYS`
* `AEVRYN_STORAGE_PROVIDER=r2`
* `AEVRYN_R2_BUCKET`
* `AEVRYN_R2_ACCOUNT_ID`
* `AEVRYN_R2_ENDPOINT_URL`
* `AEVRYN_R2_ACCESS_KEY_ID`
* `AEVRYN_R2_SECRET_ACCESS_KEY`
* `AEVRYN_SECRET_MANAGER=deployment`
* `AEVRYN_ENVIRONMENT_NAME=production`
* `AEVRYN_WORKER_RUNTIME=managed`
* `AEVRYN_WORKER_QUEUE_PROVIDER=managed`
* `AEVRYN_WORKER_API_KEY`
* `AEVRYN_WORKER_TIMEOUT_SECONDS`
* `AEVRYN_WORKER_MAX_RETRIES`
* `AEVRYN_WORKER_CONCURRENCY`
* `AEVRYN_LOG_DESTINATION=hosted`
* `AEVRYN_MONITORING_DESTINATION=hosted`
* `AEVRYN_LOG_RETENTION_DAYS`
* `AEVRYN_MONITORING_RETENTION_DAYS`
* `AEVRYN_SECURITY_ALERTS_ENABLED=true`
* `AEVRYN_METADATA_ONLY_LOGGING=true`
* `AEVRYN_IDENTITY_PROVIDER=managed`
* `AEVRYN_IDENTITY_PROVIDER_NAME=supabase`
* `AEVRYN_SUPABASE_URL`
* `AEVRYN_SUPABASE_JWKS_URL`
* `AEVRYN_SUPABASE_ANON_KEY`
* `AEVRYN_SUPABASE_SERVICE_ROLE_KEY`
* `AEVRYN_SESSION_AUTHORITY=bearer`
* `AEVRYN_SESSION_SECRET`
* `AEVRYN_PASSWORD_RESET_ENABLED=true`
* `AEVRYN_ACCOUNT_DELETION_HANDOFF_CONFIGURED=true`

This prevents accidental public startup with stateless storage, local source-byte storage, local JSON authentication, local-only secrets, in-memory worker queues, local-only logs, ambiguous monitoring, non-redacted logging posture, missing Cloudflare R2 storage credentials, missing HTTPS/HSTS edge posture, missing browser-origin policy, missing managed identity provider details, missing password reset, missing account deletion handoff, missing session secret, ambiguous environment separation, or unprotected workflow routes.

Managed production identity is not implemented yet. Production startup remains intentionally fail-closed until a managed identity adapter is selected and wired.

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
