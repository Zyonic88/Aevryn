# Aevryn V2 Phase 4 Acceptance Criteria

> Built by **Aetherra Labs**

This document defines when Version 2 Phase 4, Authentication, can be considered complete.

---

# Goal

Create a trustworthy authentication foundation so platform users can own projects without moving business logic into the website or engine.

---

# Required Capabilities

## Registration

* Accepts email, display name, and password
* Normalizes email for credential lookup
* Creates a `UserRecord` through the project repository
* Stores a password hash outside the user record
* Rejects duplicate emails
* Rejects weak passwords
* Returns a session token without exposing credential hashes

## Login

* Accepts email and password
* Verifies password hashes
* Returns a session token for valid credentials
* Rejects invalid credentials with stable errors
* Does not reveal whether email or password was wrong

## Sessions

* Issues opaque bearer tokens
* Stores token hashes, not raw tokens
* Validates active sessions
* Rejects expired sessions
* Rejects unknown sessions
* Supports current-user lookup

## Password Reset

* Issues opaque reset tokens for known users
* Stores reset token hashes, not raw reset tokens
* Completes reset with a valid unexpired token
* Replaces the password hash
* Consumes reset tokens after use
* Rejects reused reset tokens

## Boundaries

* Authentication does not own Canon
* Authentication does not own Project processing
* Authentication does not own Background Workers
* Authentication does not own frontend UI
* Authentication does not bypass the Project Database for user records

---

# Tests Required

* Unit tests for password hashing and verification
* Unit tests proving plaintext passwords are not stored
* Unit tests for registration success
* Unit tests for duplicate registration rejection
* Unit tests for login success and failure
* Unit tests for session validation
* Unit tests for expired session rejection
* Unit tests for password reset request and completion
* Unit tests proving reset tokens are single use
* Unit tests for public auth exports
* Unit tests for registration rollback cleanup
* Unit tests for duplicate session and reset token rejection
* API tests for register, login, me, and password reset routes
* API tests proving auth routes do not require deployment API keys
* API tests for unavailable auth service failures

---

# Phase 4 Complete Means

Phase 4 is complete when:

* `ruff` passes
* `mypy` passes
* `pytest` passes
* Authentication docs are complete
* Auth API endpoints are available for platform clients
* Remaining work is production adapter selection or later Phase 5 UI integration

---

# Not Phase 4

The following belong to later phases or deployment choices:

* OAuth and social login
* Teams
* Collaboration
* Payments
* Subscriptions
* Website UI
* Image generation
* Video generation
