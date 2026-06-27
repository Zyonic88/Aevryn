# Aevryn Authentication

> Built by **Aetherra Labs**

This document defines the Version 2 Phase 4 Authentication boundary.

---

# Purpose

Authentication proves who is using the Aevryn platform.

It lets creators register, log in, recover access, and access their own projects without putting identity logic inside the engine.

---

# What Is It?

Authentication is the platform identity boundary.

It manages:

* Registration
* Login
* Password hashing
* Session token issuing
* Session token validation
* Password reset token issuing
* Password reset completion
* Current authenticated user lookup
* Authentication API endpoints

---

# Why Does It Exist?

Version 2 turns Aevryn from a local engine into a usable platform.

A platform needs identity before users can own projects, imports, exports, settings, and history.

Authentication exists so the website can ask the API, "Who is this?" and the API can answer consistently.

---

# Authority Owned

The Authentication system owns:

* Credential validation
* Password hashing policy
* Password verification
* Session token lifecycle
* Password reset token lifecycle
* Authenticated user identity
* Authentication errors

---

# Authority Not Owned

Authentication does not own:

* Canon truth
* Story Import
* Entity Extraction
* Background job execution
* Project processing
* Project data rules
* Presentation view models
* Export serialization
* Website UI
* Payments
* Teams or collaboration
* Social login

---

# Core Rule

Authentication proves identity.

It does not decide canon, run jobs, parse stories, or generate outputs.

---

# Phase 4 Implementation

Phase 4 starts with a deterministic local authentication foundation:

* `PasswordHasher`
* `InMemoryCredentialStore`
* `InMemorySessionStore`
* `AuthenticationService`
* `/v2/auth/register`
* `/v2/auth/login`
* `/v2/auth/me`
* `/v2/auth/password-reset/request`
* `/v2/auth/password-reset/complete`

This proves the contract without choosing the final production identity provider or database adapter.

---

# Password Rule

Plaintext passwords are never stored.

The local foundation uses PBKDF2-HMAC-SHA256 with an explicit algorithm marker, iteration count, salt, and derived key.

Production deployments may replace the password hasher, but the API contract must not expose hashes or salts.

---

# Session Rule

Session tokens are bearer credentials.

They are returned only at login and registration time.

Stored sessions reference user IDs and expiration timestamps.

Expired sessions are invalid.

---

# Password Reset Rule

Password reset requests issue opaque reset tokens.

The reset token is a delivery artifact.

Aevryn stores only the reset token hash.

Completing a password reset consumes the token and replaces the password hash.

---

# Failure Modes

Authentication can fail if:

* Registration input is invalid
* Email is already registered
* Password is too weak
* Login credentials are invalid
* Session token is missing, invalid, or expired
* Password reset token is invalid, expired, or already consumed
* User records and credential records disagree
* Persistence fails

Failures must be explicit and must not leak password hashes or reset token hashes.

---

# V2 Phase 4 Rule

Phase 4 builds identity foundations only.

Do not build:

* Social login
* Teams
* Collaboration
* Payments
* Subscriptions
* Website UI
* Image generation
* Video generation

---

# Acceptance Standard

Authentication is Phase 4 ready when:

* Users can register
* Duplicate emails are rejected
* Passwords are hashed, not stored
* Users can log in with valid credentials
* Invalid credentials fail safely
* Session tokens can be validated
* Expired sessions fail safely
* Password reset tokens can be issued and consumed
* Reset tokens cannot be reused
* Auth API routes are discoverable
* Auth endpoints fail clearly when no service is configured
* Failed registrations roll back user and credential records
* Duplicate session and reset tokens are rejected
* Unit tests pass
* Type checks pass
* Lint checks pass
