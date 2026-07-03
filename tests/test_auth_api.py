"""Tests for Aevryn Phase 4 Authentication API endpoints."""

from __future__ import annotations

import base64
import json
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from _pytest.logging import LogCaptureFixture
from fastapi.testclient import TestClient

from aevryn.api import create_app
from aevryn.api.app import MAX_IMPORT_CONTENT_BASE64_CHARS
from aevryn.auth import (
    AuthenticationConfig,
    AuthenticationService,
    InMemoryCredentialStore,
    InMemorySessionStore,
    PasswordHasher,
)
from aevryn.import_storage import ImportContentNotFoundError, InMemoryImportContentStore
from aevryn.persistence import (
    EngineRunRecord,
    ExportRecord,
    ImportRecord,
    InMemoryProjectRepository,
    RecordNotFoundError,
    SnapshotRecord,
)
from aevryn.storage import LocalFilesystemStorage, StorageObjectNotFoundError
from aevryn.workers import InMemoryJobQueue, ProjectImportSnapshotHandler
from aevryn.workers.models import BackgroundJob

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


def test_import_inspect_requires_user_session_when_authentication_is_configured() -> None:
    """Browser import inspection should use the user session, not a deployment API key."""
    client = TestClient(
        create_app(
            api_keys=("deployment-key",),
            authentication_service=auth_service(),
        )
    )
    register_user(client, user_id="user_demo", email="demo@example.com")
    payload = {
        "source_id": "api_demo",
        "filename": "chapter.txt",
        "content_base64": import_content_base64(
            "Chapter 1\nMira checked the harbor compass."
        ),
    }

    no_session = client.post("/v2/imports/inspect", json=payload)
    with_session = client.post(
        "/v2/imports/inspect",
        headers=auth_headers("token_001"),
        json=payload,
    )

    assert no_session.status_code == 401
    assert no_session.json()["error"] == "session_required"
    assert with_session.status_code == 200
    assert with_session.json()["source_id"] == "api_demo"


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
        "storage_ref": (
            "api_import://projects/project_alpha/stories/story_alpha/"
            "imports/import_alpha"
        ),
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


def test_story_imports_api_rejects_oversized_uploads_before_storage() -> None:
    """Story imports should reject oversized source bytes before persistence."""
    repository = InMemoryProjectRepository()
    content_store = InMemoryImportContentStore()
    client = TestClient(
        create_app(
            authentication_service=auth_service(repository=repository),
            project_repository=repository,
            import_content_store=content_store,
        )
    )
    register_user(client, user_id="user_owner", email="owner@example.com")
    create_project_and_story(client)

    response = client.post(
        "/v2/projects/project_alpha/stories/story_alpha/imports",
        headers=auth_headers("token_001"),
        json={
            **import_create_payload(),
            "content_base64": "A" * (MAX_IMPORT_CONTENT_BASE64_CHARS + 4),
        },
    )

    assert response.status_code == 413
    assert response.json() == {
        "detail": "Uploaded source content exceeds the 10 MiB limit.",
        "error": "import_content_too_large",
    }
    assert repository.list_imports_for_story("user_owner", "story_alpha") == ()


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


def test_import_runs_api_can_auto_process_submitted_runs_after_response() -> None:
    """Hosted alpha bridge should return a queued run before processing it."""
    repository = InMemoryProjectRepository()
    queue = InMemoryJobQueue()
    client = TestClient(
        create_app(
            authentication_service=auth_service(repository=repository),
            project_repository=repository,
            background_job_queue=queue,
            background_job_handler=RecordingWorkerHandler(),
            auto_process_import_runs=True,
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
    assert submitted.json()["status"] == "pending"
    persisted_run = repository.get_engine_run(user_id="user_demo", run_id="run_alpha")
    assert persisted_run.status == "succeeded"
    assert persisted_run.finished_at == NOW
    assert queue.get("job_alpha").status == "succeeded"


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
    assert duplicate.json() == {
        "error": "import_run_already_active",
        "detail": "Import processing is already in progress.",
    }

    duplicate_import_run = client.post(
        "/v2/projects/project_alpha/stories/story_alpha/imports/import_alpha/runs",
        headers=auth_headers("token_001"),
        json={"run_id": "run_second", "job_id": "job_second", "now": SOON},
    )
    assert duplicate_import_run.status_code == 409
    assert duplicate_import_run.json() == {
        "error": "import_run_already_active",
        "detail": "Import processing is already in progress.",
    }

    cross_user = client.post(
        "/v2/projects/project_alpha/stories/story_alpha/imports/import_alpha/runs",
        headers=auth_headers("token_002"),
        json={"run_id": "run_other", "job_id": "job_other", "now": NOW},
    )
    assert cross_user.status_code == 404
    assert cross_user.json()["error"] == "import_not_found"


def test_delete_story_api_hard_deletes_metadata_and_import_content() -> None:
    """Story deletion should remove scoped metadata, exports, and source bytes."""
    repository = InMemoryProjectRepository()
    queue = InMemoryJobQueue()
    content_store = InMemoryImportContentStore()
    client = TestClient(
        create_app(
            authentication_service=auth_service(repository=repository),
            project_repository=repository,
            background_job_queue=queue,
            background_job_handler=ProjectImportSnapshotHandler(
                repository=repository,
                import_content_store=content_store,
            ),
            import_content_store=content_store,
        )
    )
    register_user(client, user_id="user_owner", email="owner@example.com")
    create_project_and_story(client)
    created_import = client.post(
        "/v2/projects/project_alpha/stories/story_alpha/imports",
        headers=auth_headers("token_001"),
        json=import_create_payload(),
    )
    assert created_import.status_code == 200
    storage_ref = created_import.json()["storage_ref"]
    assert content_store.read_import_content(storage_ref)
    submitted = client.post(
        "/v2/projects/project_alpha/stories/story_alpha/imports/import_alpha/runs",
        headers=auth_headers("token_001"),
        json={"run_id": "run_alpha", "job_id": "job_alpha", "now": NOW},
    )
    assert submitted.status_code == 200
    processed = client.post(
        "/v2/workers/process",
        json={"started_at": SOON, "finished_at": SOON, "max_jobs": 1},
    )
    assert processed.status_code == 200
    repository.record_export(
        ExportRecord(
            export_id="export_alpha",
            project_id="project_alpha",
            snapshot_id="snapshot_run_alpha_canon",
            export_kind="canon",
            export_format="markdown",
            filename="canon.md",
            content_type="text/markdown; charset=utf-8",
            storage_ref="storage://exports/canon.md",
            created_at="2026-06-27T00:45:00Z",
        )
    )
    assert repository.list_snapshots_for_project("user_owner", "project_alpha")
    assert repository.list_exports_for_project("user_owner", "project_alpha")

    response = client.delete(
        "/v2/projects/project_alpha/stories/story_alpha",
        headers=auth_headers("token_001"),
    )

    assert response.status_code == 204
    listed_stories = client.get(
        "/v2/projects/project_alpha/stories",
        headers=auth_headers("token_001"),
    )
    assert listed_stories.json() == {"stories": []}
    listed_runs = client.get(
        "/v2/projects/project_alpha/runs",
        headers=auth_headers("token_001"),
    )
    assert listed_runs.json() == {"runs": []}
    listed_snapshots = client.get(
        "/v2/projects/project_alpha/snapshots",
        headers=auth_headers("token_001"),
    )
    assert listed_snapshots.json() == {"snapshots": []}
    status = client.get(
        "/v2/projects/project_alpha/status",
        headers=auth_headers("token_001"),
    )
    assert status.status_code == 200
    assert status.json()["snapshots"] == {
        "available": False,
        "count": 0,
        "latest_snapshot_id": None,
        "latest_snapshot_kind": None,
    }
    assert status.json()["exports"] == {
        "available": False,
        "count": 0,
        "latest_export_id": None,
        "latest_export_kind": None,
        "latest_export_format": None,
    }
    with pytest.raises(RecordNotFoundError):
        repository.get_snapshot("user_owner", "snapshot_run_alpha_canon")
    with pytest.raises(RecordNotFoundError):
        repository.get_export("user_owner", "export_alpha")
    with pytest.raises(ImportContentNotFoundError):
        content_store.read_import_content(storage_ref)


def test_delete_project_api_hard_deletes_metadata_and_private_bytes(tmp_path: Path) -> None:
    """Project deletion should remove scoped metadata, imports, and export objects."""
    repository = InMemoryProjectRepository()
    queue = InMemoryJobQueue()
    content_store = InMemoryImportContentStore()
    storage = LocalFilesystemStorage(tmp_path / "storage")
    client = TestClient(
        create_app(
            authentication_service=auth_service(repository=repository),
            project_repository=repository,
            background_job_queue=queue,
            background_job_handler=ProjectImportSnapshotHandler(
                repository=repository,
                import_content_store=content_store,
            ),
            import_content_store=content_store,
            storage_service=storage,
        )
    )
    register_user(client, user_id="user_owner", email="owner@example.com")
    create_project_and_story(client)
    created_import = client.post(
        "/v2/projects/project_alpha/stories/story_alpha/imports",
        headers=auth_headers("token_001"),
        json=import_create_payload(),
    )
    assert created_import.status_code == 200
    import_storage_ref = created_import.json()["storage_ref"]
    submitted = client.post(
        "/v2/projects/project_alpha/stories/story_alpha/imports/import_alpha/runs",
        headers=auth_headers("token_001"),
        json={"run_id": "run_alpha", "job_id": "job_alpha", "now": NOW},
    )
    assert submitted.status_code == 200
    processed = client.post(
        "/v2/workers/process",
        json={"started_at": SOON, "finished_at": SOON, "max_jobs": 1},
    )
    assert processed.status_code == 200
    export_storage_ref = "storage://projects/project_alpha/exports/export_alpha/canon.md"
    storage.save_object(
        storage_ref=export_storage_ref,
        content=b"canon export",
        content_type="text/markdown; charset=utf-8",
        metadata={"filename": "canon.md"},
    )
    repository.record_export(
        ExportRecord(
            export_id="export_alpha",
            project_id="project_alpha",
            snapshot_id="snapshot_run_alpha_canon",
            export_kind="canon",
            export_format="markdown",
            filename="canon.md",
            content_type="text/markdown; charset=utf-8",
            storage_ref=export_storage_ref,
            created_at="2026-06-27T00:45:00Z",
        )
    )

    response = client.delete(
        "/v2/projects/project_alpha",
        headers=auth_headers("token_001"),
    )

    assert response.status_code == 204
    listed_projects = client.get("/v2/projects", headers=auth_headers("token_001"))
    assert listed_projects.json() == {"projects": []}
    missing_project = client.get(
        "/v2/projects/project_alpha",
        headers=auth_headers("token_001"),
    )
    assert missing_project.status_code == 404
    with pytest.raises(RecordNotFoundError):
        repository.get_story("user_owner", "story_alpha")
    with pytest.raises(RecordNotFoundError):
        repository.get_import("user_owner", "import_alpha")
    with pytest.raises(RecordNotFoundError):
        repository.get_engine_run("user_owner", "run_alpha")
    with pytest.raises(RecordNotFoundError):
        repository.get_snapshot("user_owner", "snapshot_run_alpha_canon")
    with pytest.raises(RecordNotFoundError):
        repository.get_export("user_owner", "export_alpha")
    with pytest.raises(ImportContentNotFoundError):
        content_store.read_import_content(import_storage_ref)
    with pytest.raises(StorageObjectNotFoundError):
        storage.read_object(export_storage_ref)


def test_phase11_project_surfaces_fail_closed_across_users() -> None:
    """Phase 11 auth boundaries should cover every owned project surface."""
    repository = InMemoryProjectRepository()
    queue = InMemoryJobQueue()
    content_store = InMemoryImportContentStore()
    client = TestClient(
        create_app(
            authentication_service=auth_service(repository=repository),
            project_repository=repository,
            background_job_queue=queue,
            background_job_handler=ProjectImportSnapshotHandler(
                repository=repository,
                import_content_store=content_store,
            ),
            import_content_store=content_store,
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
    submitted = client.post(
        "/v2/projects/project_alpha/stories/story_alpha/imports/import_alpha/runs",
        headers=auth_headers("token_001"),
        json={"run_id": "run_alpha", "job_id": "job_alpha", "now": NOW},
    )
    assert submitted.status_code == 200
    processed = client.post(
        "/v2/workers/process",
        json={"started_at": SOON, "finished_at": SOON, "max_jobs": 1},
    )
    assert processed.status_code == 200
    repository.record_export(
        ExportRecord(
            export_id="export_alpha",
            project_id="project_alpha",
            snapshot_id="snapshot_run_alpha_canon",
            export_kind="canon",
            export_format="markdown",
            filename="canon.md",
            content_type="text/markdown; charset=utf-8",
            storage_ref="storage://exports/canon.md",
            created_at="2026-06-27T00:45:00Z",
        )
    )

    owner_status = client.get(
        "/v2/projects/project_alpha/status",
        headers=auth_headers("token_001"),
    )
    assert owner_status.status_code == 200
    assert owner_status.json()["exports"]["latest_export_id"] == "export_alpha"

    cross_user_requests: list[tuple[Callable[..., Any], str, dict[str, str] | None, str]] = [
        (
            client.get,
            "/v2/projects/project_alpha",
            None,
            "project_not_found",
        ),
        (
            client.get,
            "/v2/projects/project_alpha/settings",
            None,
            "project_not_found",
        ),
        (
            client.put,
            "/v2/projects/project_alpha/settings",
            {"default_export_format": "json", "locale": "en-US"},
            "project_not_found",
        ),
        (
            client.get,
            "/v2/projects/project_alpha/stories",
            None,
            "project_not_found",
        ),
        (
            client.post,
            "/v2/projects/project_alpha/stories",
            {"story_id": "story_other", "title": "Other", "now": NOW},
            "project_not_found",
        ),
        (
            client.get,
            "/v2/projects/project_alpha/stories/story_alpha/imports",
            None,
            "story_not_found",
        ),
        (
            client.post,
            "/v2/projects/project_alpha/stories/story_alpha/imports",
            {**import_create_payload(), "import_id": "import_other"},
            "story_not_found",
        ),
        (
            client.post,
            "/v2/projects/project_alpha/stories/story_alpha/imports/import_alpha/runs",
            {"run_id": "run_other", "job_id": "job_other", "now": NOW},
            "import_not_found",
        ),
        (
            client.get,
            "/v2/projects/project_alpha/runs",
            None,
            "project_not_found",
        ),
        (
            client.get,
            "/v2/projects/project_alpha/snapshots",
            None,
            "project_not_found",
        ),
        (
            client.get,
            "/v2/projects/project_alpha/stories/story_alpha/snapshots",
            None,
            "story_not_found",
        ),
        (
            client.get,
            "/v2/projects/project_alpha/status",
            None,
            "project_not_found",
        ),
        (
            client.get,
            "/v2/projects/project_alpha/outputs",
            None,
            "project_not_found",
        ),
        (
            client.delete,
            "/v2/projects/project_alpha/stories/story_alpha",
            None,
            "story_not_found",
        ),
    ]

    for method, path, body, expected_error in cross_user_requests:
        if body is None:
            response = method(path, headers=auth_headers("token_002"))
        else:
            response = method(path, headers=auth_headers("token_002"), json=body)
        assert response.status_code == 404
        assert response.json()["error"] == expected_error
        assert "Mark carried a rusty dagger" not in response.text
        assert "export_alpha" not in response.text
        assert "storage://exports/canon.md" not in response.text


def test_phase11_privacy_logging_gate_excludes_private_story_payloads(
    caplog: LogCaptureFixture,
) -> None:
    """Workflow logs should never preserve source prose or sensitive payload text."""
    repository = InMemoryProjectRepository()
    queue = InMemoryJobQueue()
    content_store = InMemoryImportContentStore()
    client = TestClient(
        create_app(
            authentication_service=auth_service(repository=repository),
            project_repository=repository,
            background_job_queue=queue,
            background_job_handler=ProjectImportSnapshotHandler(
                repository=repository,
                import_content_store=content_store,
            ),
            import_content_store=content_store,
        )
    )
    private_markers = (
        "PRIVATE_MANUSCRIPT_SENTENCE_DO_NOT_LOG",
        "RAW_AI_RESPONSE_SECRET_DO_NOT_LOG",
        "sk-aevryn-test-secret-do-not-log",
        "C:\\Users\\creator\\private_story.txt",
        "creator-laptop.local",
    )
    private_source = "\n".join(
        (
            "Chapter 1",
            "Mark carried a dagger.",
            *private_markers,
        )
    )
    private_import_payload = {
        **import_create_payload(),
        "content_base64": base64.b64encode(private_source.encode("utf-8")).decode(
            "ascii"
        ),
    }

    with caplog.at_level(logging.DEBUG):
        register_user(client, user_id="user_owner", email="owner@example.com")
        create_project_and_story(client)
        created_import = client.post(
            "/v2/projects/project_alpha/stories/story_alpha/imports",
            headers=auth_headers("token_001"),
            json=private_import_payload,
        )
        assert created_import.status_code == 200
        submitted = client.post(
            "/v2/projects/project_alpha/stories/story_alpha/imports/import_alpha/runs",
            headers=auth_headers("token_001"),
            json={"run_id": "run_alpha", "job_id": "job_alpha", "now": NOW},
        )
        assert submitted.status_code == 200
        processed = client.post(
            "/v2/workers/process",
            json={"started_at": SOON, "finished_at": SOON, "max_jobs": 1},
        )
        assert processed.status_code == 200
        status = client.get(
            "/v2/projects/project_alpha/status",
            headers=auth_headers("token_001"),
        )
        assert status.status_code == 200
        deleted = client.delete(
            "/v2/projects/project_alpha/stories/story_alpha",
            headers=auth_headers("token_001"),
        )
        assert deleted.status_code == 204

    log_text = caplog_record_text(caplog)
    for marker in private_markers:
        assert marker not in log_text
    assert private_import_payload["content_base64"] not in log_text
    assert "serialized_output" not in log_text
    assert "session_token" not in log_text
    assert "token_001" not in log_text
    assert "token_002" not in log_text


def test_import_runs_api_allows_retry_after_stale_active_run() -> None:
    """Old alpha runs should not block retry forever."""
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

    retry = client.post(
        "/v2/projects/project_alpha/stories/story_alpha/imports/import_alpha/runs",
        headers=auth_headers("token_001"),
        json={
            "run_id": "run_retry",
            "job_id": "job_retry",
            "now": "2026-06-27T00:31:00Z",
        },
    )

    assert retry.status_code == 200
    runs = client.get(
        "/v2/projects/project_alpha/runs",
        headers=auth_headers("token_001"),
    ).json()["runs"]
    assert [run["run_id"] for run in runs] == ["run_alpha", "run_retry"]
    assert runs[0]["status"] == "failed"
    assert runs[0]["error_summary"] == "Processing timed out before completion."
    assert runs[1]["status"] == "pending"


def test_project_runs_api_marks_missing_queue_jobs_failed_after_restart() -> None:
    """Local in-memory queue loss should not leave durable runs pending forever."""
    repository = InMemoryProjectRepository()
    authentication_service = auth_service(repository=repository)
    first_queue = InMemoryJobQueue()
    client = TestClient(
        create_app(
            authentication_service=authentication_service,
            project_repository=repository,
            background_job_queue=first_queue,
        )
    )
    register_user(client, user_id="user_owner", email="owner@example.com")
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
    assert repository.get_engine_run("user_owner", "run_alpha").status == "pending"

    restarted_client = TestClient(
        create_app(
            authentication_service=authentication_service,
            project_repository=repository,
            background_job_queue=InMemoryJobQueue(),
        )
    )
    listed = restarted_client.get(
        "/v2/projects/project_alpha/runs",
        headers=auth_headers("token_001"),
    )

    assert listed.status_code == 200
    runs = listed.json()["runs"]
    assert runs[0]["run_id"] == "run_alpha"
    assert runs[0]["status"] == "failed"
    assert runs[0]["error_summary"] == (
        "Processing stopped before completion. Retry is available."
    )


def test_project_runs_api_marks_stale_running_queue_jobs_failed() -> None:
    """A stranded running queue job should not keep an import blocked forever."""
    repository = InMemoryProjectRepository()
    authentication_service = auth_service(repository=repository)
    queue = InMemoryJobQueue()
    client = TestClient(
        create_app(
            authentication_service=authentication_service,
            project_repository=repository,
            background_job_queue=queue,
        )
    )
    register_user(client, user_id="user_owner", email="owner@example.com")
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
    assert queue.claim_next(claimed_at=SOON) is not None
    assert queue.has_job("job_alpha")

    listed = client.get(
        "/v2/projects/project_alpha/runs",
        headers=auth_headers("token_001"),
    )

    assert listed.status_code == 200
    runs = listed.json()["runs"]
    assert runs[0]["run_id"] == "run_alpha"
    assert runs[0]["status"] == "failed"
    assert runs[0]["error_summary"] == (
        "Processing timed out before completion. Retry is available."
    )


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


def test_worker_process_api_drains_queued_runs() -> None:
    """Worker process API should move queued import runs through durable lifecycle."""
    repository = InMemoryProjectRepository()
    queue = InMemoryJobQueue()
    client = TestClient(
        create_app(
            authentication_service=auth_service(repository=repository),
            project_repository=repository,
            background_job_queue=queue,
            background_job_handler=RecordingWorkerHandler(),
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

    processed = client.post(
        "/v2/workers/process",
        json={"started_at": SOON, "finished_at": SOON, "max_jobs": 5},
    )

    assert processed.status_code == 200
    assert processed.json() == {
        "claimed_jobs": 1,
        "succeeded_jobs": 1,
        "failed_jobs": 0,
    }
    listed = client.get("/v2/projects/project_alpha/runs", headers=auth_headers("token_001"))
    assert listed.status_code == 200
    assert listed.json()["runs"][0]["status"] == "succeeded"
    assert listed.json()["runs"][0]["finished_at"] == SOON
    assert queue.get("job_alpha").status == "succeeded"


def test_worker_process_api_generates_snapshot_from_stored_import_content() -> None:
    """Worker processing should turn saved import bytes into durable snapshots."""
    repository = InMemoryProjectRepository()
    queue = InMemoryJobQueue()
    import_content_store = InMemoryImportContentStore()
    client = TestClient(
        create_app(
            authentication_service=auth_service(repository=repository),
            project_repository=repository,
            background_job_queue=queue,
            background_job_handler=ProjectImportSnapshotHandler(
                repository=repository,
                import_content_store=import_content_store,
            ),
            import_content_store=import_content_store,
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

    processed = client.post(
        "/v2/workers/process",
        json={"started_at": SOON, "finished_at": SOON, "max_jobs": 1},
    )

    assert processed.status_code == 200
    assert processed.json()["succeeded_jobs"] == 1
    snapshots = client.get(
        "/v2/projects/project_alpha/snapshots",
        headers=auth_headers("token_001"),
    )
    assert snapshots.status_code == 200
    assert snapshots.json()["snapshots"][0]["snapshot_id"] == "snapshot_run_alpha_canon"
    assert snapshots.json()["snapshots"][0]["snapshot_kind"] == "canon"
    assert '"source_id":"source_alpha"' in snapshots.json()["snapshots"][0]["serialized_output"]


def test_project_status_reports_metadata_only_monitoring_summary(
    caplog: LogCaptureFixture,
) -> None:
    """Project status should summarize durable workflow state without source prose."""
    repository = InMemoryProjectRepository()
    queue = InMemoryJobQueue()
    import_content_store = InMemoryImportContentStore()
    client = TestClient(
        create_app(
            authentication_service=auth_service(repository=repository),
            project_repository=repository,
            background_job_queue=queue,
            background_job_handler=ProjectImportSnapshotHandler(
                repository=repository,
                import_content_store=import_content_store,
            ),
            import_content_store=import_content_store,
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
    processed = client.post(
        "/v2/workers/process",
        json={"started_at": SOON, "finished_at": SOON, "max_jobs": 1},
    )
    assert processed.status_code == 200
    repository.record_export(
        ExportRecord(
            export_id="export_alpha",
            project_id="project_alpha",
            snapshot_id="snapshot_run_alpha_canon",
            export_kind="canon",
            export_format="markdown",
            filename="canon.md",
            content_type="text/markdown; charset=utf-8",
            storage_ref="storage://exports/canon.md",
            created_at="2026-06-27T00:45:00Z",
        )
    )

    with caplog.at_level(logging.INFO, logger="aevryn.api.app"):
        response = client.get(
            "/v2/projects/project_alpha/status",
            headers=auth_headers("token_001"),
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        "project_id": "project_alpha",
        "status": "succeeded",
        "story_count": 1,
        "import_count": 1,
        "run_count": 1,
        "latest_import": {
            "import_id": "import_alpha",
            "story_id": "story_alpha",
            "filename": "chapter_001.txt",
            "source_format": "txt",
            "created_at": NOW,
        },
        "latest_engine_run": {
            "run_id": "run_alpha",
            "story_id": "story_alpha",
            "import_id": "import_alpha",
            "status": "succeeded",
            "started_at": NOW,
            "status_updated_at": SOON,
            "finished_at": SOON,
            "error_summary": "",
            "job_ref": "queue://job_alpha",
        },
        "worker": {
            "state": "idle",
            "total_jobs": 1,
            "queued_jobs": 0,
            "running_jobs": 0,
            "succeeded_jobs": 1,
            "failed_jobs": 0,
            "next_job_id": "",
        },
        "snapshots": {
            "available": True,
            "count": 1,
            "latest_snapshot_id": "snapshot_run_alpha_canon",
            "latest_snapshot_kind": "canon",
        },
        "exports": {
            "available": True,
            "count": 1,
            "latest_export_id": "export_alpha",
            "latest_export_kind": "canon",
            "latest_export_format": "markdown",
        },
        "latest_failure_summary": "",
        "recent_workflow_events": [
            {
                "event_type": "export_created",
                "status": "succeeded",
                "occurred_at": "2026-06-27T00:45:00Z",
                "story_id": "",
                "import_id": "",
                "run_id": "",
                "snapshot_id": "snapshot_run_alpha_canon",
                "export_id": "export_alpha",
                "summary": "Created markdown canon export.",
            },
            {
                "event_type": "snapshot_created",
                "status": "succeeded",
                "occurred_at": SOON,
                "story_id": "story_alpha",
                "import_id": "",
                "run_id": "run_alpha",
                "snapshot_id": "snapshot_run_alpha_canon",
                "export_id": "",
                "summary": "Created canon snapshot.",
            },
            {
                "event_type": "engine_run",
                "status": "succeeded",
                "occurred_at": SOON,
                "story_id": "story_alpha",
                "import_id": "import_alpha",
                "run_id": "run_alpha",
                "snapshot_id": "",
                "export_id": "",
                "summary": "Run is succeeded.",
            },
            {
                "event_type": "import_saved",
                "status": "succeeded",
                "occurred_at": NOW,
                "story_id": "story_alpha",
                "import_id": "import_alpha",
                "run_id": "",
                "snapshot_id": "",
                "export_id": "",
                "summary": "Saved txt import metadata.",
            },
        ],
    }
    assert "Mark carried a rusty dagger" not in response.text
    assert "storage://exports/canon.md" not in response.text
    record = workflow_log_record(caplog, "project_status", "succeeded")
    assert_duration_log(record)
    assert getattr(record, "project_id", "") == "project_alpha"
    assert getattr(record, "project_status", "") == "succeeded"
    assert getattr(record, "story_count", 0) == 1
    assert getattr(record, "import_count", 0) == 1
    assert getattr(record, "run_count", 0) == 1
    assert getattr(record, "snapshot_count", 0) == 1
    assert getattr(record, "export_count", 0) == 1
    assert getattr(record, "worker_state", "") == "idle"
    assert "Mark carried a rusty dagger" not in caplog_record_text(caplog)
    assert "storage://exports/canon.md" not in caplog_record_text(caplog)


def test_project_status_responses_include_request_ids() -> None:
    """Project status should carry request IDs on success and error responses."""
    repository = InMemoryProjectRepository()
    client = TestClient(
        create_app(
            authentication_service=auth_service(repository=repository),
            project_repository=repository,
        )
    )
    register_user(client, user_id="user_demo", email="demo@example.com")
    create_project_and_story(client)

    success = client.get(
        "/v2/projects/project_alpha/status",
        headers={
            **auth_headers("token_001"),
            "X-Request-ID": "phase-8-status-success",
        },
    )
    missing = client.get(
        "/v2/projects/missing/status",
        headers={
            **auth_headers("token_001"),
            "X-Request-ID": "phase-8-status-error",
        },
    )

    assert success.status_code == 200
    assert success.headers["x-request-id"] == "phase-8-status-success"
    assert missing.status_code == 404
    assert missing.headers["x-request-id"] == "phase-8-status-error"
    assert missing.json()["error"] == "project_not_found"


def test_project_outputs_summarize_latest_canon_snapshot_without_source_prose() -> None:
    """Project outputs should expose processed alpha results without raw source payloads."""
    repository = InMemoryProjectRepository()
    content_store = InMemoryImportContentStore()
    client = TestClient(
        create_app(
            authentication_service=auth_service(repository=repository),
            project_repository=repository,
            import_content_store=content_store,
            background_job_queue=InMemoryJobQueue(),
            background_job_handler=ProjectImportSnapshotHandler(
                repository=repository,
                import_content_store=content_store,
            ),
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
    processed = client.post(
        "/v2/workers/process",
        json={"started_at": SOON, "finished_at": SOON, "max_jobs": 1},
    )
    assert processed.status_code == 200

    response = client.get("/v2/projects/project_alpha/outputs", headers=auth_headers("token_001"))

    assert response.status_code == 200
    payload = response.json()
    assert payload["project_id"] == "project_alpha"
    assert payload["status"] == "succeeded"
    assert payload["latest_import"]["filename"] == "chapter_001.txt"
    assert payload["latest_engine_run"]["status"] == "succeeded"
    assert payload["canon"] == {
        "available": True,
        "title": "chapter_001",
        "snapshot_kind": "canon",
        "created_at": SOON,
        "source_id": "source_alpha",
        "chapters": 1,
        "scenes": 1,
        "evidence_anchor_count": 1,
        "extraction_result_count": 1,
        "accepted_entity_count": 1,
        "accepted_fact_count": 1,
        "accepted_relationship_count": 0,
        "accepted_state_change_count": 1,
        "rejected_candidate_count": 0,
        "chapter_scene_counts": [{"chapter_index": 1, "scene_count": 1}],
    }
    assert [surface["surface"] for surface in payload["surfaces"]] == [
        "characters",
        "world",
        "timeline",
        "scenes",
        "continuity",
        "prompts",
        "exports",
    ]
    assert payload["surfaces"][0]["status"] == "ready"
    assert payload["surfaces"][1]["status"] == "waiting"
    assert payload["surfaces"][1]["summary"] == (
        "No accepted world relationships have been extracted yet."
    )
    assert payload["surfaces"][3]["item_count"] == 1
    assert payload["language_identity"] == {
        "translation_unit_count": 1,
        "translation_review_count": 0,
        "translation_review_items": [],
        "identity_decision_count": 1,
        "identity_resolved_count": 0,
        "identity_ambiguous_count": 0,
        "identity_unresolved_count": 1,
        "identity_review_items": payload["language_identity"]["identity_review_items"],
    }
    assert payload["language_identity"]["identity_review_items"] == [
        {
            "status": "unresolved",
            "chapter_id": "source_alpha_chapter_001",
            "scene_id": "source_alpha_chapter_001_scene_001",
            "evidence_anchor_id": (
                "source_alpha_chapter_001_scene_001_paragraph_001_sentence_001_anchor"
            ),
            "reference_kind": "name",
            "reference_label": "Name reference",
            "candidate_count": 0,
            "confidence": 0.0,
            "reason": "Identity could not be matched with enough evidence.",
        }
    ]
    assert payload["character_profiles"][0]["character_id"] == "character_mark"
    assert payload["character_profiles"][0]["display_name"] == "Mark"
    assert payload["character_profiles"][0]["race"]["items"] == ["Unknown"]
    assert payload["character_profiles"][0]["gender"]["items"] == ["Unknown"]
    assert payload["character_profiles"][0]["status"]["items"] == ["Unknown"]
    assert payload["world_sheet"]["entity_sections"] == []
    assert payload["scene_sheets"][0]["title"] == "Scene 1"
    assert payload["scene_sheets"][0]["chapter_label"] == "Chapter 1"
    assert payload["scene_sheets"][0]["characters_present"]["items"] == ["Mark"]
    assert payload["prompt_packs"][0]["scene"]["title"] == "Scene 1"
    assert payload["prompt_packs"][0]["image_prompt"]["title"] == "Image Prompt"
    assert payload["continuity_report"]["source_id"] == "source_alpha"
    assert payload["continuity_report"]["scenes"][0]["new"]
    assert payload["export_options"][0]["export_kind"] == "character_profile"
    assert payload["timeline_changes"] == []
    assert "Mark carried a rusty dagger" not in response.text
    assert "serialized_output" not in response.text


def test_project_outputs_identity_review_reasons_are_stable_metadata() -> None:
    """Stored resolver reasons should not leak source-adjacent prose through outputs."""
    repository = InMemoryProjectRepository()
    client = TestClient(
        create_app(
            authentication_service=auth_service(repository=repository),
            project_repository=repository,
        )
    )
    register_user(client, user_id="user_demo", email="demo@example.com")
    create_project_and_story(client)
    repository.record_import(
        ImportRecord(
            import_id="import_alpha",
            story_id="story_alpha",
            source_id="source_alpha",
            filename="chapter_001.txt",
            source_format="txt",
            storage_ref="storage://projects/project_alpha/imports/import_alpha/source.txt",
            chapter_count=1,
            scene_count=1,
            evidence_anchor_count=1,
            created_at=NOW,
        )
    )
    repository.record_engine_run(
        EngineRunRecord(
            run_id="run_alpha",
            project_id="project_alpha",
            story_id="story_alpha",
            import_id="import_alpha",
            status="succeeded",
            engine_version="aevryn_v1",
            started_at=NOW,
            status_updated_at=SOON,
            finished_at=SOON,
        )
    )
    repository.store_snapshot(
        SnapshotRecord(
            snapshot_id="snapshot_alpha",
            project_id="project_alpha",
            story_id="story_alpha",
            run_id="run_alpha",
            snapshot_kind="canon",
            content_type="application/json",
            serialized_output=json.dumps(
                {
                    "source_id": "source_alpha",
                    "title": "Alpha",
                    "chapters": 1,
                    "scenes": 1,
                    "entity_resolution": {
                        "decision_count": 1,
                        "status_counts": {"resolved": 0, "ambiguous": 1, "unresolved": 0},
                        "decisions": [
                            {
                                "status": "ambiguous",
                                "chapter_id": "source_alpha_chapter_001",
                                "scene_id": "source_alpha_chapter_001_scene_001",
                                "evidence_anchor_id": "anchor_001",
                                "reference_kind": "description",
                                "reference_label": "Description reference",
                                "candidate_count": 2,
                                "confidence": 0.58,
                                "reason": "Mark carried a rusty dagger in the original scene.",
                            }
                        ],
                    },
                }
            ),
            created_at=SOON,
        )
    )

    response = client.get("/v2/projects/project_alpha/outputs", headers=auth_headers("token_001"))

    assert response.status_code == 200
    review_items = response.json()["language_identity"]["identity_review_items"]
    assert review_items == [
        {
            "status": "ambiguous",
            "chapter_id": "source_alpha_chapter_001",
            "scene_id": "source_alpha_chapter_001_scene_001",
            "evidence_anchor_id": "anchor_001",
            "reference_kind": "description",
            "reference_label": "Description reference",
            "candidate_count": 2,
            "confidence": 0.58,
            "reason": "Identity has multiple possible matches and needs review.",
        }
    ]
    assert "Mark carried a rusty dagger" not in response.text


def test_project_outputs_translation_review_items_are_stable_metadata() -> None:
    """Translation review output should not expose source terms or issue prose."""
    repository = InMemoryProjectRepository()
    client = TestClient(
        create_app(
            authentication_service=auth_service(repository=repository),
            project_repository=repository,
        )
    )
    register_user(client, user_id="user_demo", email="demo@example.com")
    create_project_and_story(client)
    repository.record_import(
        ImportRecord(
            import_id="import_alpha",
            story_id="story_alpha",
            source_id="source_alpha",
            filename="chapter_001.txt",
            source_format="txt",
            storage_ref="storage://projects/project_alpha/imports/import_alpha/source.txt",
            chapter_count=1,
            scene_count=1,
            evidence_anchor_count=1,
            created_at=NOW,
        )
    )
    repository.record_engine_run(
        EngineRunRecord(
            run_id="run_alpha",
            project_id="project_alpha",
            story_id="story_alpha",
            import_id="import_alpha",
            status="succeeded",
            engine_version="aevryn_v1",
            started_at=NOW,
            status_updated_at=SOON,
            finished_at=SOON,
        )
    )
    repository.store_snapshot(
        SnapshotRecord(
            snapshot_id="snapshot_alpha",
            project_id="project_alpha",
            story_id="story_alpha",
            run_id="run_alpha",
            snapshot_kind="canon",
            content_type="application/json",
            serialized_output=json.dumps(
                {
                    "source_id": "source_alpha",
                    "title": "Alpha",
                    "chapters": 1,
                    "scenes": 1,
                    "translation": {
                        "unit_count": 1,
                        "issue_count": 1,
                        "units": [
                            {
                                "unit_id": "translation_source_alpha_chapter_001_scene_001",
                                "source_language": "zh",
                                "target_language": "en",
                                "mode": "clean_english",
                                "source_chapter_id": "source_alpha_chapter_001",
                                "source_scene_id": "source_alpha_chapter_001_scene_001",
                                "source_evidence_anchor_ids": ["anchor_001"],
                                "issue_count": 1,
                                "issues": [
                                    {
                                        "issue_code": "translation_review_required",
                                        "issue_label": "Glossary term needs review",
                                        "evidence_anchor_count": 1,
                                        "source_term": "private_source_term",
                                        "message": "Private issue prose.",
                                    }
                                ],
                            }
                        ],
                    },
                }
            ),
            created_at=SOON,
        )
    )

    response = client.get("/v2/projects/project_alpha/outputs", headers=auth_headers("token_001"))

    assert response.status_code == 200
    summary = response.json()["language_identity"]
    assert summary["translation_review_count"] == 1
    assert summary["translation_review_items"] == [
        {
            "issue_code": "translation_review_required",
            "issue_label": "Glossary term needs review",
            "chapter_id": "source_alpha_chapter_001",
            "scene_id": "source_alpha_chapter_001_scene_001",
            "evidence_anchor_count": 1,
            "reason": "Aevryn preserved an uncertain term for review.",
        }
    ]
    assert "private_source_term" not in response.text
    assert "Private issue prose" not in response.text


def test_project_outputs_humanize_legacy_presentation_machine_ids() -> None:
    """Older snapshots should not expose raw extraction IDs in output surfaces."""
    repository = InMemoryProjectRepository()
    client = TestClient(
        create_app(
            authentication_service=auth_service(repository=repository),
            project_repository=repository,
        )
    )
    register_user(client, user_id="user_demo", email="demo@example.com")
    create_project_and_story(client)
    repository.record_import(
        ImportRecord(
            import_id="import_alpha",
            story_id="story_alpha",
            source_id="source_alpha",
            filename="chapter_001.txt",
            source_format="txt",
            storage_ref="storage://projects/project_alpha/imports/import_alpha/source.txt",
            chapter_count=1,
            scene_count=1,
            evidence_anchor_count=1,
            created_at=NOW,
        )
    )
    repository.record_engine_run(
        EngineRunRecord(
            run_id="run_alpha",
            project_id="project_alpha",
            story_id="story_alpha",
            import_id="import_alpha",
            status="succeeded",
            engine_version="aevryn_v1",
            started_at=NOW,
            status_updated_at=SOON,
            finished_at=SOON,
        )
    )
    repository.store_snapshot(
        SnapshotRecord(
            snapshot_id="snapshot_alpha",
            project_id="project_alpha",
            story_id="story_alpha",
            run_id="run_alpha",
            snapshot_kind="canon",
            content_type="application/json",
            serialized_output=json.dumps(_legacy_machine_id_snapshot_payload()),
            created_at=SOON,
        )
    )

    response = client.get("/v2/projects/project_alpha/outputs", headers=auth_headers("token_001"))

    assert response.status_code == 200
    payload = response.json()
    assert payload["world_sheet"]["entity_sections"][0]["items"] == [
        "Zhao Chen is located in North Star Academy"
    ]
    assert payload["prompt_packs"][0]["image_prompt"]["items"] == [
        "Character: Zhao Chen"
    ]
    assert payload["continuity_report"]["scenes"][0]["updated"][0]["description"] == (
        "State changed at this scene."
    )
    assert "Character: Zhao Chen (E1)" not in response.text
    assert "State Valid From Event" not in response.text
    assert "Aevryn Import Bundle" not in response.text


def test_worker_process_api_fails_when_import_content_is_missing() -> None:
    """Worker processing should not fabricate snapshots without source bytes."""
    repository = InMemoryProjectRepository()
    queue = InMemoryJobQueue()
    missing_content_store = InMemoryImportContentStore()
    client = TestClient(
        create_app(
            authentication_service=auth_service(repository=repository),
            project_repository=repository,
            background_job_queue=queue,
            background_job_handler=ProjectImportSnapshotHandler(
                repository=repository,
                import_content_store=missing_content_store,
            ),
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

    processed = client.post(
        "/v2/workers/process",
        json={"started_at": SOON, "finished_at": SOON, "max_jobs": 1},
    )

    assert processed.status_code == 200
    assert processed.json()["failed_jobs"] == 1
    runs = client.get("/v2/projects/project_alpha/runs", headers=auth_headers("token_001"))
    assert runs.status_code == 200
    assert runs.json()["runs"][0]["status"] == "failed"
    snapshots = client.get(
        "/v2/projects/project_alpha/snapshots",
        headers=auth_headers("token_001"),
    )
    assert snapshots.status_code == 200
    assert snapshots.json()["snapshots"] == []


def test_worker_process_api_requires_configured_handler() -> None:
    """Worker process API should fail clearly when execution is unavailable."""
    repository = InMemoryProjectRepository()
    client = TestClient(
        create_app(
            authentication_service=auth_service(repository=repository),
            project_repository=repository,
            background_job_queue=InMemoryJobQueue(),
        )
    )

    response = client.post(
        "/v2/workers/process",
        json={"started_at": NOW, "finished_at": NOW, "max_jobs": 1},
    )

    assert response.status_code == 503
    assert response.json()["error"] == "background_worker_unavailable"


def test_worker_process_api_uses_deployment_api_key_when_configured() -> None:
    """Internal worker routes should remain workflow API-key protected."""
    repository = InMemoryProjectRepository()
    client = TestClient(
        create_app(
            api_keys=("deployment-key",),
            authentication_service=auth_service(repository=repository),
            project_repository=repository,
            background_job_queue=InMemoryJobQueue(),
            background_job_handler=RecordingWorkerHandler(),
        )
    )

    unauthorized = client.post(
        "/v2/workers/process",
        json={"started_at": NOW, "finished_at": NOW, "max_jobs": 1},
    )
    authorized = client.post(
        "/v2/workers/process",
        headers={"X-Aevryn-API-Key": "deployment-key"},
        json={"started_at": NOW, "finished_at": NOW, "max_jobs": 1},
    )

    assert unauthorized.status_code == 401
    assert unauthorized.json()["error"] == "authentication_required"
    assert authorized.status_code == 200
    assert authorized.json()["claimed_jobs"] == 0


def test_worker_snapshot_api_stores_and_lists_completed_run_outputs() -> None:
    """Worker snapshots should persist only after a run succeeds and list by scope."""
    repository = InMemoryProjectRepository()
    queue = InMemoryJobQueue()
    client = TestClient(
        create_app(
            authentication_service=auth_service(repository=repository),
            project_repository=repository,
            background_job_queue=queue,
            background_job_handler=RecordingWorkerHandler(),
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
    processed = client.post(
        "/v2/workers/process",
        json={"started_at": SOON, "finished_at": SOON, "max_jobs": 1},
    )
    assert processed.status_code == 200

    stored = client.post(
        "/v2/workers/runs/run_alpha/snapshots",
        json={
            "snapshot_id": "snapshot_alpha",
            "snapshot_kind": "character_profile",
            "content_type": "application/json",
            "serialized_output": '{"character_id":"character_mark"}',
            "now": SOON,
        },
    )

    assert stored.status_code == 200
    assert stored.json()["project_id"] == "project_alpha"
    assert stored.json()["story_id"] == "story_alpha"
    assert stored.json()["run_id"] == "run_alpha"
    project_list = client.get(
        "/v2/projects/project_alpha/snapshots",
        headers=auth_headers("token_001"),
    )
    assert project_list.status_code == 200
    assert [snapshot["snapshot_id"] for snapshot in project_list.json()["snapshots"]] == [
        "snapshot_alpha"
    ]
    story_list = client.get(
        "/v2/projects/project_alpha/stories/story_alpha/snapshots?snapshot_kind=character_profile",
        headers=auth_headers("token_001"),
    )
    assert story_list.status_code == 200
    assert story_list.json()["snapshots"][0]["serialized_output"] == (
        '{"character_id":"character_mark"}'
    )


def test_project_export_api_creates_lists_and_downloads_storage_backed_export(
    tmp_path: Path,
) -> None:
    """Project exports should write bytes to Storage and return metadata only."""
    repository = InMemoryProjectRepository()
    client = TestClient(
        create_app(
            authentication_service=auth_service(repository),
            project_repository=repository,
            storage_service=LocalFilesystemStorage(tmp_path / "storage"),
        )
    )
    register_user(client, user_id="user_demo", email="demo@example.com")
    create_project_and_story(client)
    _store_succeeded_snapshot(repository)

    created = client.post(
        "/v2/projects/project_alpha/exports",
        headers=auth_headers("token_001"),
        json={
            "export_id": "export_alpha",
            "snapshot_id": "snapshot_alpha",
            "export_format": "json",
            "filename": "canon.json",
            "now": SOON,
        },
    )

    assert created.status_code == 200
    payload = created.json()
    assert payload == {
        "export_id": "export_alpha",
        "project_id": "project_alpha",
        "snapshot_id": "snapshot_alpha",
        "export_kind": "canon",
        "export_format": "json",
        "filename": "canon.json",
        "content_type": "application/json",
        "size": len('{"accepted_fact_count":1}'),
        "checksum": payload["checksum"],
        "created_at": SOON,
    }
    assert payload["checksum"].startswith("sha256:")
    assert "storage_ref" not in payload
    assert "storage://projects" not in created.text

    listed = client.get(
        "/v2/projects/project_alpha/exports",
        headers=auth_headers("token_001"),
    )
    assert listed.status_code == 200
    assert listed.json()["exports"] == [payload]

    downloaded = client.get(
        "/v2/projects/project_alpha/exports/export_alpha/download",
        headers=auth_headers("token_001"),
    )
    assert downloaded.status_code == 200
    assert downloaded.text == '{"accepted_fact_count":1}'
    assert downloaded.headers["content-type"] == "application/json"
    assert downloaded.headers["content-disposition"] == (
        'attachment; filename="canon.json"'
    )


def test_project_export_api_rejects_cross_user_reads(tmp_path: Path) -> None:
    """Export metadata and bytes must stay inside project ownership boundaries."""
    repository = InMemoryProjectRepository()
    client = TestClient(
        create_app(
            authentication_service=auth_service(repository),
            project_repository=repository,
            storage_service=LocalFilesystemStorage(tmp_path / "storage"),
        )
    )
    register_user(client, user_id="user_demo", email="demo@example.com")
    register_user(client, user_id="user_other", email="other@example.com")
    create_project_and_story(client)
    _store_succeeded_snapshot(repository)
    created = client.post(
        "/v2/projects/project_alpha/exports",
        headers=auth_headers("token_001"),
        json={
            "export_id": "export_alpha",
            "snapshot_id": "snapshot_alpha",
            "export_format": "json",
            "now": SOON,
        },
    )
    assert created.status_code == 200

    listed = client.get(
        "/v2/projects/project_alpha/exports",
        headers=auth_headers("token_002"),
    )
    downloaded = client.get(
        "/v2/projects/project_alpha/exports/export_alpha/download",
        headers=auth_headers("token_002"),
    )

    assert listed.status_code == 404
    assert listed.json()["error"] == "project_not_found"
    assert downloaded.status_code == 404
    assert downloaded.json()["error"] == "export_not_found"
    assert "storage://projects" not in listed.text
    assert "storage://projects" not in downloaded.text


def test_project_export_api_rejects_unsupported_snapshot_export_format(
    tmp_path: Path,
) -> None:
    """The first persisted export route should stay narrow until formats are added."""
    repository = InMemoryProjectRepository()
    client = TestClient(
        create_app(
            authentication_service=auth_service(repository),
            project_repository=repository,
            storage_service=LocalFilesystemStorage(tmp_path / "storage"),
        )
    )
    register_user(client, user_id="user_demo", email="demo@example.com")
    create_project_and_story(client)
    _store_succeeded_snapshot(repository)

    response = client.post(
        "/v2/projects/project_alpha/exports",
        headers=auth_headers("token_001"),
        json={
            "export_id": "export_alpha",
            "snapshot_id": "snapshot_alpha",
            "export_format": "markdown",
            "now": SOON,
        },
    )

    assert response.status_code == 400
    assert response.json()["error"] == "export_create_failed"
    assert "Only json snapshot exports" in response.json()["detail"]


def test_worker_snapshot_api_rejects_incomplete_runs_and_invalid_kinds() -> None:
    """Snapshot writes and filters should fail before unsafe records are persisted."""
    repository = InMemoryProjectRepository()
    client = TestClient(
        create_app(
            authentication_service=auth_service(repository=repository),
            project_repository=repository,
            background_job_queue=InMemoryJobQueue(),
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

    incomplete = client.post(
        "/v2/workers/runs/run_alpha/snapshots",
        json={
            "snapshot_id": "snapshot_alpha",
            "snapshot_kind": "canon",
            "content_type": "application/json",
            "serialized_output": "{}",
            "now": SOON,
        },
    )
    invalid_filter = client.get(
        "/v2/projects/project_alpha/stories/story_alpha/snapshots?snapshot_kind=bad_kind",
        headers=auth_headers("token_001"),
    )

    assert incomplete.status_code == 400
    assert incomplete.json()["error"] == "snapshot_store_failed"
    assert invalid_filter.status_code == 400
    assert invalid_filter.json()["error"] == "invalid_snapshot_kind"


def test_worker_snapshot_api_uses_deployment_api_key_when_configured() -> None:
    """Trusted worker snapshot writes should remain deployment API-key protected."""
    repository = InMemoryProjectRepository()
    client = TestClient(
        create_app(
            api_keys=("deployment-key",),
            authentication_service=auth_service(repository=repository),
            project_repository=repository,
        )
    )

    unauthorized = client.post(
        "/v2/workers/runs/run_missing/snapshots",
        json={
            "snapshot_id": "snapshot_alpha",
            "snapshot_kind": "canon",
            "content_type": "application/json",
            "serialized_output": "{}",
            "now": SOON,
        },
    )
    authorized = client.post(
        "/v2/workers/runs/run_missing/snapshots",
        headers={"X-Aevryn-API-Key": "deployment-key"},
        json={
            "snapshot_id": "snapshot_alpha",
            "snapshot_kind": "canon",
            "content_type": "application/json",
            "serialized_output": "{}",
            "now": SOON,
        },
    )

    assert unauthorized.status_code == 401
    assert unauthorized.json()["error"] == "authentication_required"
    assert authorized.status_code == 404
    assert authorized.json()["error"] == "run_not_found"


def test_project_snapshot_api_rejects_cross_user_reads() -> None:
    """Snapshot lists should not leak projects or stories across users."""
    repository = InMemoryProjectRepository()
    queue = InMemoryJobQueue()
    client = TestClient(
        create_app(
            authentication_service=auth_service(repository=repository),
            project_repository=repository,
            background_job_queue=queue,
            background_job_handler=RecordingWorkerHandler(),
        )
    )
    register_user(client, user_id="user_demo", email="demo@example.com")
    register_user(client, user_id="user_other", email="other@example.com")
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
    processed = client.post(
        "/v2/workers/process",
        json={"started_at": SOON, "finished_at": SOON, "max_jobs": 1},
    )
    assert processed.status_code == 200
    stored = client.post(
        "/v2/workers/runs/run_alpha/snapshots",
        json={
            "snapshot_id": "snapshot_alpha",
            "snapshot_kind": "canon",
            "content_type": "application/json",
            "serialized_output": "{}",
            "now": SOON,
        },
    )
    assert stored.status_code == 200

    project_list = client.get(
        "/v2/projects/project_alpha/snapshots",
        headers=auth_headers("token_002"),
    )
    story_list = client.get(
        "/v2/projects/project_alpha/stories/story_alpha/snapshots",
        headers=auth_headers("token_002"),
    )

    assert project_list.status_code == 404
    assert project_list.json()["error"] == "project_not_found"
    assert story_list.status_code == 404
    assert story_list.json()["error"] == "story_not_found"


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
    assert "/v2/projects/{project_id}/snapshots" in route_paths
    assert "/v2/projects/{project_id}/outputs" in route_paths
    assert "/v2/projects/{project_id}/stories/{story_id}/snapshots" in route_paths
    assert "/v2/projects/{project_id}/stories/{story_id}/imports" in route_paths
    assert "/v2/projects/{project_id}/runs" in route_paths
    assert "/v2/projects/{project_id}/stories/{story_id}/imports/{import_id}/runs" in route_paths
    assert "/v2/workers/process" in route_paths
    assert "/v2/workers/runs/{run_id}/snapshots" in route_paths

    paths = client.get("/openapi.json").json()["paths"]
    assert paths["/v2/projects"]["get"]["operationId"] == "getV2Projects"
    assert paths["/v2/projects"]["post"]["operationId"] == "postV2Projects"
    assert paths["/v2/projects/{project_id}"]["get"]["operationId"] == "getV2Project"
    assert paths["/v2/projects/{project_id}"]["delete"]["operationId"] == "deleteV2Project"
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
    assert paths["/v2/projects/{project_id}/snapshots"]["get"]["operationId"] == (
        "getV2ProjectSnapshots"
    )
    assert paths["/v2/projects/{project_id}/outputs"]["get"]["operationId"] == (
        "getV2ProjectOutputs"
    )
    assert paths["/v2/projects/{project_id}/stories/{story_id}/snapshots"]["get"][
        "operationId"
    ] == "getV2StorySnapshots"
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
    assert paths["/v2/workers/process"]["post"]["operationId"] == "postV2WorkersProcess"
    assert paths["/v2/workers/runs/{run_id}/snapshots"]["post"]["operationId"] == (
        "postV2WorkerRunSnapshots"
    )


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


def _legacy_machine_id_snapshot_payload() -> dict[str, object]:
    """Return old-style presentation metadata with visible machine IDs."""
    section = {"title": "Unknown", "items": ["Unknown"]}
    scene = {
        "scene_id": "source_alpha_chapter_001_scene_001",
        "title": "Scene 1",
        "chapter_label": "Chapter 1",
        "location": section,
        "characters_present": {"title": "Characters Present", "items": ["Zhao Chen"]},
        "mood": section,
        "purpose": section,
        "visual_highlights": section,
        "continuity_changes": section,
        "environment": section,
        "evidence_summary": "1 verified evidence references",
    }
    return {
        "source_id": "source_alpha",
        "title": "Alpha",
        "chapters": 1,
        "scenes": 1,
        "scene_ids": ("source_alpha_chapter_001_scene_001",),
        "accepted_entity_count": 1,
        "accepted_fact_count": 1,
        "accepted_relationship_count": 1,
        "accepted_state_change_count": 1,
        "presentation": {
            "characters": [
                {
                    "character_id": "E1",
                    "display_name": "Zhao Chen",
                    "subtitle": "Unknown",
                    "race": section,
                    "gender": section,
                    "status": section,
                    "current_goal": section,
                    "current_equipment": section,
                    "current_abilities": section,
                    "current_assets": section,
                    "territory": section,
                    "relationships": section,
                    "current_limitations": section,
                    "recent_changes": section,
                    "evidence_summary": "1 verified facts",
                }
            ],
            "world": {
                "chapter_label": "Chapter 1",
                "entity_sections": [
                    {
                        "title": "North Star Academy (location)",
                        "items": ["E5 part_of E5", "E1 located_in E5"],
                    }
                ],
                "evidence_summary": "1 verified evidence references",
            },
            "scenes": [scene],
            "prompt_packs": [
                {
                    "scene": scene,
                    "image_prompt": {
                        "title": "Image Prompt",
                        "items": ["Character: Zhao Chen (E1)"],
                    },
                    "narration_prompt": section,
                    "camera_prompt": section,
                    "animation_prompt": section,
                }
            ],
            "continuity_report": {
                "source_id": "source_alpha",
                "scenes": [
                    {
                        "scene_id": "source_alpha_chapter_001_scene_001",
                        "new": [],
                        "updated": [
                            {
                                "record_id": "record_alpha",
                                "record_type": "state",
                                "description": (
                                    "State Valid From Event Fact E1 Current Location "
                                    "North Star Academy Evidence Aevryn Import Bundle "
                                    "Chapter 001 Scene 001 Paragraph 001 Sentence 001 Anchor"
                                ),
                                "evidence_id": "anchor_alpha",
                                "chapter_id": "source_alpha_chapter_001",
                                "scene_id": "source_alpha_chapter_001_scene_001",
                            }
                        ],
                        "still_known": [],
                        "invalidated": [],
                    }
                ],
            },
            "export_options": [],
        },
    }


def _store_succeeded_snapshot(repository: InMemoryProjectRepository) -> None:
    """Store import, succeeded run, and canon snapshot test metadata."""
    repository.record_import(
        ImportRecord(
            import_id="import_alpha",
            story_id="story_alpha",
            source_id="source_alpha",
            filename="chapter_001.txt",
            source_format="txt",
            storage_ref="storage://projects/project_alpha/imports/import_alpha/source.txt",
            chapter_count=1,
            scene_count=1,
            evidence_anchor_count=1,
            created_at=NOW,
        )
    )
    repository.record_engine_run(
        EngineRunRecord(
            run_id="run_alpha",
            project_id="project_alpha",
            story_id="story_alpha",
            import_id="import_alpha",
            status="succeeded",
            engine_version="aevryn_v1",
            started_at=NOW,
            status_updated_at=SOON,
            finished_at=SOON,
        )
    )
    repository.store_snapshot(
        SnapshotRecord(
            snapshot_id="snapshot_alpha",
            project_id="project_alpha",
            story_id="story_alpha",
            run_id="run_alpha",
            snapshot_kind="canon",
            content_type="application/json",
            serialized_output='{"accepted_fact_count":1}',
            created_at=SOON,
        )
    )


class RecordingWorkerHandler:
    """Worker handler used by API tests."""

    def process(self, _job: BackgroundJob) -> None:
        """Accept one queued background job."""


def auth_headers(token: str) -> dict[str, str]:
    """Return authorization headers for API tests."""
    return {"Authorization": f"Bearer {token}", "X-Aevryn-Now": SOON}


def import_content_base64(text: str) -> str:
    """Return base64-encoded import source for API tests."""
    return base64.b64encode(text.encode("utf-8")).decode("ascii")



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


def workflow_log_record(
    caplog: LogCaptureFixture,
    workflow_kind: str,
    workflow_status: str,
) -> logging.LogRecord:
    """Return one captured API workflow log record."""
    for record in caplog.records:
        if (
            getattr(record, "workflow_kind", "") == workflow_kind
            and getattr(record, "workflow_status", "") == workflow_status
        ):
            return record
    raise AssertionError(f"Missing workflow log: {workflow_kind}/{workflow_status}")


def assert_duration_log(record: logging.LogRecord) -> None:
    """Assert a workflow log record has metadata-only duration."""
    duration_ms = getattr(record, "duration_ms", None)
    assert isinstance(duration_ms, float)
    assert duration_ms >= 0.0


def caplog_record_text(caplog: LogCaptureFixture) -> str:
    """Return captured log metadata as searchable text."""
    return "\n".join(str(record.__dict__) for record in caplog.records)
