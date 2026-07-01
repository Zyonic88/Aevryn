# Aevryn Cloudflare Pages Deployment

> Built by **Aetherra Labs**

This document defines the first Cloudflare Pages deployment path for the Aevryn web app.

It is a release-candidate deployment runbook, not public-beta approval.

---

# Status

```text
Deployment target: Cloudflare Pages
Status: Deployed - hosted frontend/API header smoke passed
Public beta: Blocked
```

The hosted API is available at `https://api.aevryn.ai/v2/health`.

The hosted frontend is available at `https://app.aevryn.ai`.

The frontend must be deployed with:

```text
VITE_AEVRYN_API_URL=https://api.aevryn.ai
```

---

# Core Rule

```text
Frontend owns presentation. API owns workflow state. Storage and secrets never move into the browser.
```

The hosted frontend may call the public API origin.

It must not contain:

* API keys
* Cloudflare R2 credentials
* database URLs
* Supabase service-role keys
* worker keys
* session secrets
* manuscript bytes outside user-selected browser upload flow

---

# Deployment Shape

```text
Cloudflare Pages
-> app.aevryn.ai
-> browser
-> https://api.aevryn.ai
-> Cloud Run API
```

The Cloud Run API CORS policy currently allows:

```text
https://app.aevryn.ai
```

Do not deploy a production frontend to another origin unless Cloud Run CORS is deliberately updated.

---

# Required Cloudflare Permissions

For Wrangler deployment, use a Cloudflare API token with the narrowest available permissions for the Aevryn account.

Recommended token scope:

```text
Account - Cloudflare Pages - Edit
Account resource - Aetherra Project
```

If the token will also configure custom domains or DNS, add only the minimum required DNS permissions for `aevryn.ai`.

Do not paste tokens into source files, docs, GitHub issues, or logs.

---

# Local Production Build

From the repository root:

```powershell
cd C:\Users\enigm\Documents\Aevryn\web
$env:VITE_AEVRYN_API_URL="https://api.aevryn.ai"
npm.cmd run build
```

Expected result:

```text
dist/ generated successfully
```

Optional local frontend gates:

```powershell
npm.cmd run lint
npm.cmd run test
```

---

# Wrangler Direct Upload Path

Use this path for the first release-candidate smoke if the Cloudflare Pages dashboard is not yet connected to GitHub.

Authenticate Wrangler in the current PowerShell session:

```powershell
$env:CLOUDFLARE_API_TOKEN="<stored outside repo>"
```

Create the Pages project once:

```powershell
npx.cmd wrangler pages project create aevryn-web --production-branch master
```

Build and deploy:

```powershell
cd C:\Users\enigm\Documents\Aevryn\web
$env:VITE_AEVRYN_API_URL="https://api.aevryn.ai"
npm.cmd run build
npx.cmd wrangler pages deploy dist --project-name aevryn-web --branch master
```

Record the Pages deployment URL returned by Wrangler.

---

# Git-Connected Pages Path

Use this path for repeatable release-candidate and beta deployments.

Recommended Cloudflare Pages settings:

```text
Project name: aevryn-web
Production branch: master
Root directory: web
Build command: npm.cmd run build
Build output directory: dist
Environment variable: VITE_AEVRYN_API_URL=https://api.aevryn.ai
```

If Cloudflare's Linux builder is used, the build command may be:

```text
npm run build
```

Do not configure secrets in the frontend Pages environment unless a future browser-safe public value is explicitly required.

---

# Custom Domain

Target frontend domain:

```text
app.aevryn.ai
```

Add `app.aevryn.ai` as a Cloudflare Pages custom domain for the `aevryn-web` project.

Expected result:

```text
https://app.aevryn.ai loads the Aevryn web app over HTTPS.
```

---

# Hosted Frontend Smoke

After deployment, verify:

```powershell
curl.exe -I https://app.aevryn.ai
curl.exe -I https://api.aevryn.ai/v2/health
```

Then use a browser to verify:

* login/register page loads
* dashboard loads
* dashboard API health uses `https://api.aevryn.ai`
* CORS succeeds from `https://app.aevryn.ai`
* protected routes still require authentication
* errors remain creator-facing and metadata-only
* no secrets or source prose appear in browser console output

Hosted frontend/API header smoke result:

```text
Date: 2026-07-01
Pages project: aevryn-web
Preview URL: https://84f1e9e9.aevryn-web.pages.dev
Custom domain: https://app.aevryn.ai
Result: https://app.aevryn.ai returned HTTP OK
API CORS result: https://api.aevryn.ai/v2/health allowed Origin https://app.aevryn.ai
Secrets printed: 0
```

---

# Public Beta Decision

```text
Public beta: Blocked
Reason: Cloudflare Pages frontend/API header smoke passed, but managed identity and creator workflow smoke have not passed.
```
