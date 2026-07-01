# Aevryn Cloud Run Deployment

> Built by **Aetherra Labs**

This document defines the first Google Cloud Run deployment path for the Aevryn API.

It is a release-candidate deployment runbook, not public-beta approval.

---

# Status

```text
Deployment target: Google Cloud Run
Status: Deployed - health smoke passed
Public beta: Blocked
```

The local production-style smoke has passed for production config, PostgreSQL Project Database, and Cloudflare R2.

Hosted Cloud Run API health smoke has passed.

Hosted custom-domain API health smoke has passed.

Hosted browser/API, managed-identity, and workflow smoke are still required.

Cloudflare Pages frontend deployment is tracked in `docs/AEVRYN_CLOUDFLARE_PAGES_DEPLOYMENT.md`.

---

# Core Rule

```text
Cloud Run owns API runtime. Cloudflare owns edge, DNS, R2, and email. Database and identity remain managed services.
```

The Cloud Run service must not store manuscripts on the container filesystem.

The container filesystem is ephemeral.

Aevryn source bytes belong in private R2.

Project metadata belongs in PostgreSQL.

Identity belongs to Supabase.

Secrets belong in Google Secret Manager or Cloud Run secret bindings.

---

# Deployment Shape

```text
Cloudflare Pages
-> app.aevryn.ai
-> browser
-> api.aevryn.ai
-> Cloud Run service
-> PostgreSQL Project Database
-> Cloudflare R2 private bucket
-> Supabase Auth
```

Cloudflare remains responsible for DNS, TLS edge posture, WAF/rate-limit policy, R2 storage, email routing, and email sending.

Cloud Run is responsible only for the Aevryn API container runtime.

---

# Required Google APIs

The Google Cloud project must enable:

```powershell
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

These correspond to:

* Cloud Run Admin API
* Artifact Registry API
* Cloud Build API
* Secret Manager API

---

# Container Contract

The repository root contains:

* `Dockerfile`
* `.dockerignore`

The container installs the platform, PostgreSQL, object-storage, and identity extras:

```text
.[platform,postgresql,object-storage,identity]
```

The container starts the API with:

```text
python -m aevryn.cli api --host 0.0.0.0 --port ${PORT:-8080} --allowed-origin ${AEVRYN_API_ALLOWED_ORIGINS:-https://app.aevryn.ai}
```

Cloud Run provides `PORT`.

The default expected port is `8080`.

---

# Artifact Registry

Recommended first release-candidate values:

```text
Region: us-central1
Artifact Registry repository: aevryn-api
Cloud Run service: aevryn-api
Image tag: rc
```

Create the Artifact Registry repository:

```powershell
gcloud artifacts repositories create aevryn-api `
  --repository-format=docker `
  --location=us-central1 `
  --description="Aevryn API containers"
```

Build and push the image:

```powershell
gcloud builds submit `
  --tag us-central1-docker.pkg.dev/YOUR_PROJECT_ID/aevryn-api/aevryn-api:rc
```

Do not include local env files in the Docker context.

`.dockerignore` excludes local env files, local runtime data, caches, build outputs, snapshots, and web build artifacts.

---

# Runtime Environment

Non-secret Cloud Run environment variables:

```text
AEVRYN_DEPLOYMENT_ENV=production
AEVRYN_ENVIRONMENT_NAME=production
AEVRYN_SECRET_MANAGER=deployment
AEVRYN_PROJECT_DATABASE_ADAPTER=postgresql
AEVRYN_STORAGE_PROVIDER=r2
AEVRYN_R2_BUCKET=aevryn-dev
AEVRYN_R2_ACCOUNT_ID=<account-id>
AEVRYN_R2_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
AEVRYN_PUBLIC_FRONTEND_BASE_URL=https://app.aevryn.ai
AEVRYN_PUBLIC_API_BASE_URL=https://api.aevryn.ai
AEVRYN_API_ALLOWED_ORIGINS=https://app.aevryn.ai
AEVRYN_HTTPS_ONLY=true
AEVRYN_HSTS_ENABLED=true
AEVRYN_IDENTITY_PROVIDER=managed
AEVRYN_IDENTITY_PROVIDER_NAME=supabase
AEVRYN_SUPABASE_URL=https://<project-ref>.supabase.co
AEVRYN_SUPABASE_JWKS_URL=https://<project-ref>.supabase.co/auth/v1/.well-known/jwks.json
AEVRYN_SESSION_AUTHORITY=bearer
AEVRYN_PASSWORD_RESET_ENABLED=true
AEVRYN_ACCOUNT_DELETION_HANDOFF_CONFIGURED=true
AEVRYN_WORKER_RUNTIME=managed
AEVRYN_WORKER_QUEUE_PROVIDER=managed
AEVRYN_WORKER_TIMEOUT_SECONDS=120
AEVRYN_WORKER_MAX_RETRIES=3
AEVRYN_WORKER_CONCURRENCY=1
AEVRYN_LOG_DESTINATION=hosted
AEVRYN_MONITORING_DESTINATION=hosted
AEVRYN_LOG_RETENTION_DAYS=30
AEVRYN_MONITORING_RETENTION_DAYS=30
AEVRYN_SECURITY_ALERTS_ENABLED=true
AEVRYN_METADATA_ONLY_LOGGING=true
```

Secret-backed Cloud Run variables:

```text
AEVRYN_PROJECT_DATABASE_URL
AEVRYN_API_KEYS
AEVRYN_R2_ACCESS_KEY_ID
AEVRYN_R2_SECRET_ACCESS_KEY
AEVRYN_SUPABASE_ANON_KEY
AEVRYN_SUPABASE_SERVICE_ROLE_KEY
AEVRYN_SESSION_SECRET
AEVRYN_WORKER_API_KEY
```

Do not put secret values in:

* source files
* docs
* GitHub issues
* Cloud Build substitutions
* command history when avoidable
* logs
* support bundles

---

# First Deploy

Deploy the service after the image exists and secrets are configured:

```powershell
gcloud run deploy aevryn-api `
  --image us-central1-docker.pkg.dev/YOUR_PROJECT_ID/aevryn-api/aevryn-api:rc `
  --region us-central1 `
  --platform managed `
  --port 8080 `
  --allow-unauthenticated `
  --set-env-vars AEVRYN_DEPLOYMENT_ENV=production,AEVRYN_ENVIRONMENT_NAME=production,AEVRYN_SECRET_MANAGER=deployment,AEVRYN_PROJECT_DATABASE_ADAPTER=postgresql,AEVRYN_STORAGE_PROVIDER=r2,AEVRYN_R2_BUCKET=aevryn-dev,AEVRYN_R2_ACCOUNT_ID=YOUR_R2_ACCOUNT_ID,AEVRYN_R2_ENDPOINT_URL=https://YOUR_R2_ACCOUNT_ID.r2.cloudflarestorage.com,AEVRYN_PUBLIC_FRONTEND_BASE_URL=https://app.aevryn.ai,AEVRYN_PUBLIC_API_BASE_URL=https://api.aevryn.ai,AEVRYN_API_ALLOWED_ORIGINS=https://app.aevryn.ai,AEVRYN_HTTPS_ONLY=true,AEVRYN_HSTS_ENABLED=true,AEVRYN_IDENTITY_PROVIDER=managed,AEVRYN_IDENTITY_PROVIDER_NAME=supabase,AEVRYN_SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co,AEVRYN_SUPABASE_JWKS_URL=https://YOUR_PROJECT_REF.supabase.co/auth/v1/.well-known/jwks.json,AEVRYN_SESSION_AUTHORITY=bearer,AEVRYN_PASSWORD_RESET_ENABLED=true,AEVRYN_ACCOUNT_DELETION_HANDOFF_CONFIGURED=true,AEVRYN_WORKER_RUNTIME=managed,AEVRYN_WORKER_QUEUE_PROVIDER=managed,AEVRYN_WORKER_TIMEOUT_SECONDS=120,AEVRYN_WORKER_MAX_RETRIES=3,AEVRYN_WORKER_CONCURRENCY=1,AEVRYN_LOG_DESTINATION=hosted,AEVRYN_MONITORING_DESTINATION=hosted,AEVRYN_LOG_RETENTION_DAYS=30,AEVRYN_MONITORING_RETENTION_DAYS=30,AEVRYN_SECURITY_ALERTS_ENABLED=true,AEVRYN_METADATA_ONLY_LOGGING=true `
  --set-secrets AEVRYN_PROJECT_DATABASE_URL=AEVRYN_PROJECT_DATABASE_URL:latest,AEVRYN_API_KEYS=AEVRYN_API_KEYS:latest,AEVRYN_R2_ACCESS_KEY_ID=AEVRYN_R2_ACCESS_KEY_ID:latest,AEVRYN_R2_SECRET_ACCESS_KEY=AEVRYN_R2_SECRET_ACCESS_KEY:latest,AEVRYN_SUPABASE_ANON_KEY=AEVRYN_SUPABASE_ANON_KEY:latest,AEVRYN_SUPABASE_SERVICE_ROLE_KEY=AEVRYN_SUPABASE_SERVICE_ROLE_KEY:latest,AEVRYN_SESSION_SECRET=AEVRYN_SESSION_SECRET:latest,AEVRYN_WORKER_API_KEY=AEVRYN_WORKER_API_KEY:latest
```

`--allow-unauthenticated` allows browsers to reach the API.

Aevryn route-level authentication and authorization still protect user workflows.

Cloudflare WAF/rate limits should be added before public beta.

---

# Hosted Smoke

After deploy, record the Cloud Run URL and run:

```powershell
curl.exe https://YOUR_CLOUD_RUN_URL/v2/health
```

Expected result:

```text
HTTP 200
status=ok
storage.project_storage=configured
storage.import_content_storage=configured
```

Then run the browser/API smoke through `https://api.aevryn.ai` after the custom domain is mapped.

The hosted smoke must verify:

* `/v2/health` works over HTTPS
* CORS allows only `https://app.aevryn.ai`
* protected routes still require managed identity
* workflow errors remain metadata-only
* logs do not contain manuscripts, credentials, tokens, private URLs, hostnames, usernames, or machine-local paths
* R2 storage references work without exposing R2 credentials to the frontend

Hosted health smoke result:

```text
Date: 2026-07-01
Service: aevryn-api
Region: us-central1
Revision: aevryn-api-00003-9v4
Service URL: https://aevryn-api-561437810621.us-central1.run.app
Result: /v2/health returned HTTP OK
Header/status check: HTTP OK
Secrets printed: 0
```

Custom-domain health smoke result:

```text
Date: 2026-07-01
Domain: api.aevryn.ai
Mapping: Cloud Run domain mapping to aevryn-api
DNS: api CNAME ghs.googlehosted.com.
Certificate: Google-managed certificate provisioned
Result: https://api.aevryn.ai/v2/health returned HTTP OK
Header/status check: HTTP OK
Secrets printed: 0
```

Remaining hosted smoke:

```text
Cloudflare Pages frontend is not connected to the hosted API.
Local frontend production build passed with VITE_AEVRYN_API_URL=https://api.aevryn.ai.
Managed identity browser flow has not been smoke-tested against Cloud Run.
Creator workflow smoke has not been run against Cloud Run.
```

---

# Custom Domain

Target API domain:

```text
api.aevryn.ai
```

Map the Cloud Run service to the custom domain in Google Cloud.

Then create or adjust the DNS record in Cloudflare according to the mapping instructions Google provides.

Do not route public beta traffic until the hosted smoke has passed and the release-candidate record is signed.

---

# Public Beta Decision

```text
Public beta: Blocked
Reason: Cloud Run API health smoke and custom-domain API health smoke passed, but frontend, managed-identity, and workflow smoke have not passed.
```
