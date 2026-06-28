"""Tests for Aevryn Phase 4 Authentication API endpoints."""

from __future__ import annotations

import base64

from fastapi.testclient import TestClient

from aevryn.api import create_app
from aevryn.auth import (
    AuthenticationConfig,
    AuthenticationService,
    InMemoryCredentialStore,
    InMemorySessionStore,
    PasswordHasher,
)
from aevryn.persistence import InMemoryProjectRepository
from aevryn.workers import InMemoryJobQueue

NOW = "2026-06-27T00:00:00Z"
SOON = "2026-06-27T00:30:00Z"
PASSWORD = "StrongPass123"
NEW_PASSWORD = "BetterPass456"


def test_auth_register_login_me_and_reset_flow() -> None:
    """Authentication API should expose the Phase 4 identity flow."""
    client = TestClient(create_app(authentication_service=auth_service()))

    register = client.post(
        "/v2/auth/register",
        json={
            "user_id": "user_demo",
            "email": "Demo@Example.com",
            "display_name": "Demo User",
            "password": PASSWORD,
            "now": NOW,
        },
    )

    assert register.status_code == 200
    register_payload = register.json()
    assert register_payload["user_id"] == "user_demo"
    assert register_payload["email"] == "demo@example.com"
    assert register_payload["session_token"] == "token_001"

    me = client.get(
        "/v2/auth/me",
        headers={
            "Authorization": "Bearer token_001",
            "X-Aevryn-Now": SOON,
        },
    )
    assert me.status_code == 200
    assert me.json() == {
        "user_id": "user_demo",
        "email": "demo@example.com",
        "display_name": "Demo User",
    }

    login = client.post(
        "/v2/auth/login",
        json={"email": "demo@example.com", "password": PASSWORD, "now": NOW},
    )
    assert login.status_code == 200
    assert login.json()["session_token"] == "token_002"

    reset = client.post(
        "/v2/auth/password-reset/request",
        json={"email": "demo@example.com", "reset_id": "reset_demo", "now": NOW},
    )
    assert reset.status_code == 200
    assert reset.json()["reset_token"] == "token_003"

    completed = client.post(
        "/v2/auth/password-reset/complete",
        json={
            "reset_token": "token_003",
            "new_password": NEW_PASSWORD,
            "now": SOON,
        },
    )
    assert completed.status_code == 200
    assert completed.json() == {"status": "password_reset_complete"}

    old_login = client.post(
        "/v2/auth/login",
        json={"email": "demo@example.com", "password": PASSWORD, "now": SOON},
    )
    assert old_login.status_code == 401
    assert old_login.json()["error"] == "invalid_credentials"

    new_login = client.post(
        "/v2/auth/login",
        json={"email": "demo@example.com", "password": NEW_PASSWORD, "now": SOON},
    )
    assert new_login.status_code == 200


def test_auth_endpoints_do_not_require_deployment_api_key() -> None:
    """Auth endpoints should remain public even when workflow API keys are configured."""
    client = TestClient(
        create_app(
            api_keys=("deployment-key",),
            authentication_service=auth_service(),
        )
    )

    response = client.post(
        "/v2/auth/register",
        json={
            "user_id": "user_demo",
            "email": "demo@example.com",
            "display_name": "Demo User",
            "password": PASSWORD,
            "now": NOW,
        },
    )

    assert response.status_code == 200
    assert response.json()["session_token"] == "token_001"


def test_auth_api_reports_unavailable_service() -> None:
    """Auth endpoints should fail clearly when no auth service is configured."""
    client = TestClient(create_app())

    response = client.post(
        "/v2/auth/login",
        json={"email": "demo@example.com", "password": PASSWORD, "now": NOW},
    )

    assert response.status_code == 503
    assert response.json() == {
        "error": "authentication_unavailable",
        "detail": "Authentication service is not configured.",
    }


def test_auth_api_rejects_invalid_session_and_missing_time() -> None:
    """The me endpoint should require an active session and validation time."""
    client = TestClient(create_app(authentication_service=auth_service()))

    no_token = client.get("/v2/auth/me", headers={"X-Aevryn-Now": SOON})
    assert no_token.status_code == 401
    assert no_token.json()["error"] == "session_required"

    no_time = client.get("/v2/auth/me", headers={"Authorization": "Bearer token_001"})
    assert no_time.status_code == 400
    assert no_time.json()["error"] == "missing_time"

    invalid = client.get(
        "/v2/auth/me",
        headers={"Authorization": "Bearer missing", "X-Aevryn-Now": SOON},
    )
    assert invalid.status_code == 401
    assert invalid.json()["error"] == "invalid_session"


def test_auth_api_rejects_password_policy_failures() -> None:
    """Auth API should expose stable password policy errors."""
    client = TestClient(create_app(authentication_service=auth_service()))

    response = client.post(
        "/v2/auth/register",
        json={
            "user_id": "user_demo",
            "email": "demo@example.com",
            "display_name": "Demo User",
            "password": "short",
            "now": NOW,
        },
    )

    assert response.status_code == 400
    assert response.json()["error"] == "password_policy_failed"


def test_auth_routes_are_reported_in_capabilities_and_openapi() -> None:
    """Auth API routes should be discoverable through platform metadata."""
    client = TestClient(create_app(authentication_service=auth_service()))

    capabilities = client.get("/v2/capabilities")
    assert capabilities.status_code == 200
    route_paths = {route["path"] for route in capabilities.json()["routes"]}
    assert "/v2/auth/register" in route_paths
    assert "/v2/auth/login" in route_paths
    assert "/v2/auth/me" in route_paths
    assert "/v2/auth/password-reset/request" in route_paths
    assert "/v2/auth/password-reset/complete" in route_paths

    paths = client.get("/openapi.json").json()["paths"]
    assert paths["/v2/auth/register"]["post"]["operationId"] == (
        "postV2AuthRegister"
    )
    assert paths["/v2/auth/me"]["get"]["operationId"] == "getV2AuthMe"


def test_project_storage_api_creates_lists_and_loads_projects() -> None:
    """Project storage API should persist project metadata behind auth."""
    repository = InMemoryProjectRepository()
    client = TestClient(
        create_app(
            authentication_service=auth_service(repository=repository),
            project_repository=repository,
        )
    )
    register_user(client, user_id="user_demo", email="demo@example.com")

    created = client.post(
        "/v2/projects",
        headers=auth_headers("token_001"),
        json={
            "project_id": "project_alpha",
            "name": "  Alpha   Project  ",
            "now": NOW,
        },
    )

    assert created.status_code == 200
    assert created.json() == {
        "project_id": "project_alpha",
        "name": "Alpha Project",
        "created_at": NOW,
        "updated_at": NOW,
    }

    listed = client.get("/v2/projects", headers=auth_headers("token_001"))
    assert listed.status_code == 200
    assert listed.json()["projects"] == [created.json()]

    loaded = client.get("/v2/projects/project_alpha", headers=auth_headers("token_001"))
    assert loaded.status_code == 200
    assert loaded.json() == created.json()


def test_project_storage_api_does_not_require_deployment_api_key() -> None:
    """Project storage routes should use bearer sessions, not workflow API keys."""
    repository = InMemoryProjectRepository()
    client = TestClient(
        create_app(
            api_keys=("deployment-key",),
            authentication_service=auth_service(repository=repository),
            project_repository=repository,
        )
    )
    register_user(client, user_id="user_demo", email="demo@example.com")

    created = client.post(
        "/v2/projects",
        headers=auth_headers("token_001"),
        json={"project_id": "project_alpha", "name": "Alpha", "now": NOW},
    )

    assert created.status_code == 200
    assert created.json()["project_id"] == "project_alpha"


def test_project_settings_api_reads_and_updates_settings() -> None:
    """Project settings API should default and persist project-level settings."""
    repository = InMemoryProjectRepository()
    client = TestClient(
        create_app(
            authentication_service=auth_service(repository=repository),
            project_repository=repository,
        )
    )
    register_user(client, user_id="user_demo", email="demo@example.com")
    created = client.post(
        "/v2/projects",
        headers=auth_headers("token_001"),
        json={"project_id": "project_alpha", "name": "Alpha", "now": NOW},
    )
    assert created.status_code == 200

    default_settings = client.get(
        "/v2/projects/project_alpha/settings",
        headers=auth_headers("token_001"),
    )
    assert default_settings.status_code == 200
    assert default_settings.json() == {
        "project_id": "project_alpha",
        "default_export_format": "markdown",
        "locale": "en-US",
    }

    updated = client.put(
        "/v2/projects/project_alpha/settings",
        headers=auth_headers("token_001"),
        json={"default_export_format": " JSON ", "locale": " en-GB "},
    )
    assert updated.status_code == 200
    assert updated.json() == {
        "project_id": "project_alpha",
        "default_export_format": "json",
        "locale": "en-GB",
    }

    reloaded = client.get(
        "/v2/projects/project_alpha/settings",
        headers=auth_headers("token_001"),
    )
    assert reloaded.status_code == 200
    assert reloaded.json() == updated.json()


def test_project_settings_api_rejects_invalid_and_cross_user_updates() -> None:
    """Project settings writes should validate payloads and ownership."""
    repository = InMemoryProjectRepository()
    client = TestClient(
        create_app(
            authentication_service=auth_service(repository=repository),
            project_repository=repository,
        )
    )
    register_user(client, user_id="user_owner", email="owner@example.com")
    register_user(client, user_id="user_other", email="other@example.com")
    created = client.post(
        "/v2/projects",
        headers=auth_headers("token_001"),
        json={"project_id": "project_alpha", "name": "Alpha", "now": NOW},
    )
    assert created.status_code == 200

    cross_user = client.put(
        "/v2/projects/project_alpha/settings",
        headers=auth_headers("token_002"),
        json={"default_export_format": "json", "locale": "en-US"},
    )
    assert cross_user.status_code == 404
    assert cross_user.json()["error"] == "project_not_found"

    invalid = client.put(
        "/v2/projects/project_alpha/settings",
        headers=auth_headers("token_001"),
        json={"default_export_format": "bad format", "locale": "en-US"},
    )
    assert invalid.status_code == 400
    assert invalid.json()["error"] == "project_settings_failed"


def test_project_stories_api_creates_and_lists_stories() -> None:
    """Project stories API should persist story metadata behind auth."""
    repository = InMemoryProjectRepository()
    client = TestClient(
        create_app(
            authentication_service=auth_service(repository=repository),
            project_repository=repository,
        )
    )
    register_user(client, user_id="user_demo", email="demo@example.com")
    created_project = client.post(
        "/v2/projects",
        headers=auth_headers("token_001"),
        json={"project_id": "project_alpha", "name": "Alpha", "now": NOW},
    )
    assert created_project.status_code == 200

    empty = client.get("/v2/projects/project_alpha/stories", headers=auth_headers("token_001"))
    assert empty.status_code == 200
    assert empty.json() == {"stories": []}

    created = client.post(
        "/v2/projects/project_alpha/stories",
        headers=auth_headers("token_001"),
        json={"story_id": "story_alpha", "title": "  Alpha   Story  ", "now": NOW},
    )
    assert created.status_code == 200
    assert created.json() == {
        "story_id": "story_alpha",
        "project_id": "project_alpha",
        "title": "Alpha Story",
        "created_at": NOW,
        "updated_at": NOW,
    }

    listed = client.get("/v2/projects/project_alpha/stories", headers=auth_headers("token_001"))
    assert listed.status_code == 200
    assert listed.json()["stories"] == [created.json()]


def test_project_stories_api_rejects_duplicate_and_cross_user_writes() -> None:
    """Project stories API should enforce identity and project ownership."""
    repository = InMemoryProjectRepository()
    client = TestClient(
        create_app(
            authentication_service=auth_service(repository=repository),
            project_repository=repository,
        )
    )
    register_user(client, user_id="user_owner", email="owner@example.com")
    register_user(client, user_id="user_other", email="other@example.com")
    project = client.post(
        "/v2/projects",
        headers=auth_headers("token_001"),
        json={"project_id": "project_alpha", "name": "Alpha", "now": NOW},
    )
    assert project.status_code == 200
    payload = {"story_id": "story_alpha", "title": "Alpha", "now": NOW}
    created = client.post(
        "/v2/projects/project_alpha/stories",
        headers=auth_headers("token_001"),
        json=payload,
    )
    assert created.status_code == 200

    duplicate = client.post(
        "/v2/projects/project_alpha/stories",
        headers=auth_headers("token_001"),
        json=payload,
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"] == "story_exists"

    cross_user = client.post(
        "/v2/projects/project_alpha/stories",
        headers=auth_headers("token_002"),
        json={"story_id": "story_other", "title": "Other", "now": NOW},
    )
    assert cross_user.status_code == 404
    assert cross_user.json()["error"] == "project_not_found"


def test_story_imports_api_creates_and_lists_import_metadata() -> None:
    """Story imports API should inspect source and persist metadata behind auth."""
    repository = InMemoryProjectRepository()
    client = TestClient(
        create_app(
            authentication_service=auth_service(repository=repository),
            project_repository=repository,
        )
    )
    register_user(client, user_id="user_demo", email="demo@example.com")
    create_project_and_story(client)

    empty = client.get(
        "/v2/projects/project_alpha/stories/story_alpha/imports",
        headers=auth_headers("token_001"),
    )
    assert empty.status_code == 200
    assert empty.json() == {"imports": []}

    created = client.post(
        "/v2/projects/project_alpha/stories/story_alpha/imports",
        headers=auth_headers("token_001"),
        json=import_create_payload(),
    )
    assert created.status_code == 200
    assert created.json() == {
        "import_id": "import_alpha",
        "story_id": "story_alpha",
        "source_id": "source_alpha",
        "filename": "chapter_001.txt",
        "source_format": "txt",
        "storage_ref": "api_import://story_alpha/import_alpha",
        "chapter_count": 1,
        "scene_count": 1,
        "evidence_anchor_count": 1,
        "created_at": NOW,
    }

    listed = client.get(
        "/v2/projects/project_alpha/stories/story_alpha/imports",
        headers=auth_headers("token_001"),
    )
    assert listed.status_code == 200
    assert listed.json()["imports"] == [created.json()]


def test_story_imports_api_rejects_duplicate_and_cross_user_writes() -> None:
    """Story imports API should preserve identity and ownership boundaries."""
    repository = InMemoryProjectRepository()
    client = TestClient(
        create_app(
            authentication_service=auth_service(repository=repository),
            project_repository=repository,
        )
    )
    register_user(client, user_id="user_owner", email="owner@example.com")
    register_user(client, user_id="user_other", email="other@example.com")
    create_project_and_story(client)

    created = client.post(
        "/v2/projects/project_alpha/stories/story_alpha/imports",
        headers=auth_headers("token_001"),
        json=import_create_payload(),
    )
    assert created.status_code == 200

    duplicate = client.post(
        "/v2/projects/project_alpha/stories/story_alpha/imports",
        headers=auth_headers("token_001"),
        json=import_create_payload(),
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"] == "import_exists"

    cross_user = client.post(
        "/v2/projects/project_alpha/stories/story_alpha/imports",
        headers=auth_headers("token_002"),
        json={**import_create_payload(), "import_id": "import_other"},
    )
    assert cross_user.status_code == 404
    assert cross_user.json()["error"] == "story_not_found"

    wrong_project = client.get(
        "/v2/projects/project_missing/stories/story_alpha/imports",
        headers=auth_headers("token_001"),
    )
    assert wrong_project.status_code == 404
    assert wrong_project.json()["error"] == "story_not_found"


def test_import_runs_api_submits_and_lists_pending_runs() -> None:
    """Import run API should persist pending run metadata and enqueue jobs."""
    repository = InMemoryProjectRepository()
    queue = InMemoryJobQueue()
    client = TestClient(
        create_app(
            authentication_service=auth_service(repository=repository),
            project_repository=repository,
            background_job_queue=queue,
        )
    )
    register_user(client, user_id="user_demo", email="demo@example.com")
    create_project_and_story(client)
    created_import = client.post(
        "/v2/projects/project_alpha/stories/story_alpha/imports",
        headers=auth_headers("token_001"),
        json=import_create_payload(),
    )
    assert created_import.status_code == 200

    submitted = client.post(
        "/v2/projects/project_alpha/stories/story_alpha/imports/import_alpha/runs",
        headers=auth_headers("token_001"),
        json={"run_id": "run_alpha", "job_id": "job_alpha", "now": NOW},
    )
    assert submitted.status_code == 200
    assert submitted.json() == {
        "run_id": "run_alpha",
        "project_id": "project_alpha",
        "story_id": "story_alpha",
        "import_id": "import_alpha",
        "status": "pending",
        "engine_version": "aevryn_v1",
        "started_at": NOW,
        "status_updated_at": NOW,
        "finished_at": None,
        "error_summary": "",
        "job_ref": "queue://job_alpha",
    }
    assert queue.get("job_alpha").run_id == "run_alpha"

    listed = client.get("/v2/projects/project_alpha/runs", headers=auth_headers("token_001"))
    assert listed.status_code == 200
    assert listed.json()["runs"] == [submitted.json()]


def test_import_runs_api_rejects_duplicate_and_cross_user_submissions() -> None:
    """Import run API should preserve identity and project ownership boundaries."""
    repository = InMemoryProjectRepository()
    queue = InMemoryJobQueue()
    client = TestClient(
        create_app(
            authentication_service=auth_service(repository=repository),
            project_repository=repository,
            background_job_queue=queue,
        )
    )
    register_user(client, user_id="user_owner", email="owner@example.com")
    register_user(client, user_id="user_other", email="other@example.com")
    create_project_and_story(client)
    created_import = client.post(
        "/v2/projects/project_alpha/stories/story_alpha/imports",
        headers=auth_headers("token_001"),
        json=import_create_payload(),
    )
    assert created_import.status_code == 200
    payload = {"run_id": "run_alpha", "job_id": "job_alpha", "now": NOW}

    submitted = client.post(
        "/v2/projects/project_alpha/stories/story_alpha/imports/import_alpha/runs",
        headers=auth_headers("token_001"),
        json=payload,
    )
    assert submitted.status_code == 200

    duplicate = client.post(
        "/v2/projects/project_alpha/stories/story_alpha/imports/import_alpha/runs",
        headers=auth_headers("token_001"),
        json=payload,
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"] == "run_exists"

    cross_user = client.post(
        "/v2/projects/project_alpha/stories/story_alpha/imports/import_alpha/runs",
        headers=auth_headers("token_002"),
        json={"run_id": "run_other", "job_id": "job_other", "now": NOW},
    )
    assert cross_user.status_code == 404
    assert cross_user.json()["error"] == "import_not_found"


def test_import_runs_api_requires_configured_queue() -> None:
    """Import run submission should fail clearly when no queue is configured."""
    repository = InMemoryProjectRepository()
    client = TestClient(
        create_app(
            authentication_service=auth_service(repository=repository),
            project_repository=repository,
        )
    )
    register_user(client, user_id="user_demo", email="demo@example.com")
    create_project_and_story(client)
    created_import = client.post(
        "/v2/projects/project_alpha/stories/story_alpha/imports",
        headers=auth_headers("token_001"),
        json=import_create_payload(),
    )
    assert created_import.status_code == 200

    response = client.post(
        "/v2/projects/project_alpha/stories/story_alpha/imports/import_alpha/runs",
        headers=auth_headers("token_001"),
        json={"run_id": "run_alpha", "job_id": "job_alpha", "now": NOW},
    )

    assert response.status_code == 503
    assert response.json()["error"] == "background_queue_unavailable"


def test_project_storage_api_requires_configured_storage() -> None:
    """Project routes should fail clearly when no repository is configured."""
    client = TestClient(create_app(authentication_service=auth_service()))

    response = client.get("/v2/projects", headers=auth_headers("token_001"))

    assert response.status_code == 503
    assert response.json() == {
        "error": "project_storage_unavailable",
        "detail": "Project storage is not configured.",
    }


def test_project_storage_api_requires_authentication() -> None:
    """Project routes should require a bearer session."""
    repository = InMemoryProjectRepository()
    client = TestClient(
        create_app(
            authentication_service=auth_service(repository=repository),
            project_repository=repository,
        )
    )

    response = client.get("/v2/projects", headers={"X-Aevryn-Now": SOON})

    assert response.status_code == 401
    assert response.json()["error"] == "session_required"


def test_project_storage_api_rejects_cross_user_project_reads() -> None:
    """Project detail reads must not cross ownership boundaries."""
    repository = InMemoryProjectRepository()
    client = TestClient(
        create_app(
            authentication_service=auth_service(repository=repository),
            project_repository=repository,
        )
    )
    register_user(client, user_id="user_owner", email="owner@example.com")
    register_user(client, user_id="user_other", email="other@example.com")
    created = client.post(
        "/v2/projects",
        headers=auth_headers("token_001"),
        json={"project_id": "project_alpha", "name": "Alpha", "now": NOW},
    )
    assert created.status_code == 200

    response = client.get("/v2/projects/project_alpha", headers=auth_headers("token_002"))

    assert response.status_code == 404
    assert response.json() == {
        "error": "project_not_found",
        "detail": "Project not found.",
    }


def test_project_storage_api_rejects_duplicate_project_ids() -> None:
    """Project creation should surface duplicate project identities clearly."""
    repository = InMemoryProjectRepository()
    client = TestClient(
        create_app(
            authentication_service=auth_service(repository=repository),
            project_repository=repository,
        )
    )
    register_user(client, user_id="user_demo", email="demo@example.com")
    payload = {"project_id": "project_alpha", "name": "Alpha", "now": NOW}
    first = client.post("/v2/projects", headers=auth_headers("token_001"), json=payload)
    assert first.status_code == 200

    duplicate = client.post("/v2/projects", headers=auth_headers("token_001"), json=payload)

    assert duplicate.status_code == 409
    assert duplicate.json()["error"] == "project_exists"


def test_project_storage_routes_are_reported_in_capabilities_and_openapi() -> None:
    """Project storage routes should be discoverable through API metadata."""
    repository = InMemoryProjectRepository()
    client = TestClient(
        create_app(
            authentication_service=auth_service(repository=repository),
            project_repository=repository,
        )
    )

    capabilities = client.get("/v2/capabilities")
    route_paths = {route["path"] for route in capabilities.json()["routes"]}
    assert "/v2/projects" in route_paths
    assert "/v2/projects/{project_id}" in route_paths
    assert "/v2/projects/{project_id}/settings" in route_paths
    assert "/v2/projects/{project_id}/stories" in route_paths
    assert "/v2/projects/{project_id}/stories/{story_id}/imports" in route_paths
    assert "/v2/projects/{project_id}/runs" in route_paths
    assert "/v2/projects/{project_id}/stories/{story_id}/imports/{import_id}/runs" in route_paths

    paths = client.get("/openapi.json").json()["paths"]
    assert paths["/v2/projects"]["get"]["operationId"] == "getV2Projects"
    assert paths["/v2/projects"]["post"]["operationId"] == "postV2Projects"
    assert paths["/v2/projects/{project_id}"]["get"]["operationId"] == "getV2Project"
    assert paths["/v2/projects/{project_id}/settings"]["get"]["operationId"] == (
        "getV2ProjectSettings"
    )
    assert paths["/v2/projects/{project_id}/settings"]["put"]["operationId"] == (
        "putV2ProjectSettings"
    )
    assert paths["/v2/projects/{project_id}/stories"]["get"]["operationId"] == (
        "getV2ProjectStories"
    )
    assert paths["/v2/projects/{project_id}/stories"]["post"]["operationId"] == (
        "postV2ProjectStories"
    )
    assert paths["/v2/projects/{project_id}/stories/{story_id}/imports"]["get"][
        "operationId"
    ] == "getV2StoryImports"
    assert paths["/v2/projects/{project_id}/stories/{story_id}/imports"]["post"][
        "operationId"
    ] == "postV2StoryImports"
    assert paths["/v2/projects/{project_id}/runs"]["get"]["operationId"] == (
        "getV2ProjectRuns"
    )
    assert paths["/v2/projects/{project_id}/stories/{story_id}/imports/{import_id}/runs"]["post"][
        "operationId"
    ] == "postV2ImportRuns"


def register_user(client: TestClient, *, user_id: str, email: str) -> None:
    """Register one deterministic user for project API tests."""
    response = client.post(
        "/v2/auth/register",
        json={
            "user_id": user_id,
            "email": email,
            "display_name": "Demo User",
            "password": PASSWORD,
            "now": NOW,
        },
    )
    assert response.status_code == 200


def create_project_and_story(client: TestClient) -> None:
    """Create deterministic project and story parents for API tests."""
    created_project = client.post(
        "/v2/projects",
        headers=auth_headers("token_001"),
        json={"project_id": "project_alpha", "name": "Alpha", "now": NOW},
    )
    assert created_project.status_code == 200
    created_story = client.post(
        "/v2/projects/project_alpha/stories",
        headers=auth_headers("token_001"),
        json={"story_id": "story_alpha", "title": "Alpha Story", "now": NOW},
    )
    assert created_story.status_code == 200


def import_create_payload() -> dict[str, str]:
    """Return a deterministic import create payload."""
    return {
        "import_id": "import_alpha",
        "source_id": "source_alpha",
        "filename": "chapter_001.txt",
        "content_base64": base64.b64encode(b"Chapter 1\nMark carried a dagger.").decode("ascii"),
        "title": "Alpha Source",
        "now": NOW,
    }


def auth_headers(token: str) -> dict[str, str]:
    """Return authorization headers for API tests."""
    return {"Authorization": f"Bearer {token}", "X-Aevryn-Now": SOON}



def auth_service(
    repository: InMemoryProjectRepository | None = None,
) -> AuthenticationService:
    """Return a deterministic authentication service for API tests."""
    token_factory = TokenFactory()
    return AuthenticationService(
        repository=repository or InMemoryProjectRepository(),
        credential_store=InMemoryCredentialStore(),
        session_store=InMemorySessionStore(),
        password_hasher=PasswordHasher(iterations=10),
        token_factory=token_factory.next_token,
        config=AuthenticationConfig(session_duration_seconds=3600, reset_duration_seconds=3600),
    )


class TokenFactory:
    """Deterministic token factory for auth API tests."""

    def __init__(self) -> None:
        """Create a token counter."""
        self._index = 0

    def next_token(self) -> str:
        """Return the next stable token."""
        self._index += 1
        return f"token_{self._index:03d}"
