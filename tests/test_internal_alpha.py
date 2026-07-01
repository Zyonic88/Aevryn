"""Tests for Phase 10 internal alpha planning contracts."""

from __future__ import annotations

import base64
from dataclasses import replace
from pathlib import Path

from fastapi.testclient import TestClient

from aevryn.api import create_app
from aevryn.auth import (
    AuthenticationConfig,
    AuthenticationService,
    InMemoryCredentialStore,
    InMemorySessionStore,
    PasswordHasher,
)
from aevryn.import_storage import InMemoryImportContentStore
from aevryn.performance_runner import run_local_v2_performance_baseline
from aevryn.persistence import InMemoryProjectRepository
from aevryn.workers import InMemoryJobQueue, ProjectImportSnapshotHandler

ROOT = Path(__file__).resolve().parents[1]
NOW = "2026-06-27T00:00:00Z"
SOON = "2026-06-27T00:30:00Z"
PASSWORD = "StrongPass123"


def test_phase10_internal_alpha_docs_define_private_readiness_boundary() -> None:
    """Phase 10 docs should define private alpha scope before implementation."""
    alpha_doc = (ROOT / "docs" / "AEVRYN_INTERNAL_ALPHA.md").read_text(
        encoding="utf-8"
    )
    acceptance_doc = (
        ROOT / "docs" / "AEVRYN_V2_PHASE_10_ACCEPTANCE.md"
    ).read_text(encoding="utf-8")

    assert "Use it." in alpha_doc
    assert "Do not launch it publicly." in alpha_doc
    assert "Register\n-> Create Project\n-> Upload Story" in alpha_doc
    assert "backend owns workflow state" in alpha_doc
    assert "performance metadata stays outside canon" in alpha_doc
    assert "# Automated Gates" in alpha_doc
    assert "# Manual Alpha Checks" in alpha_doc
    assert "# Recovery" in alpha_doc
    assert "Can the user continue?" in alpha_doc
    assert "# Readiness Test Ladder" in alpha_doc
    assert "docs/AEVRYN_INTERNAL_ALPHA_CHECKLIST.md" in alpha_doc
    assert "Smoke Test" in alpha_doc
    assert "Integration Test" in alpha_doc
    assert "Operational Readiness Test" in alpha_doc
    assert "Release Candidate Test" in alpha_doc
    assert "Manual checks must not expand Phase 10" in alpha_doc
    assert "Phase 10 is accepted when:" in acceptance_doc
    assert "Recovery is covered as its own readiness layer" in acceptance_doc
    assert "Aevryn validation passes." in acceptance_doc
    assert "public launch" in acceptance_doc


def test_phase10_internal_alpha_checklist_versions_readiness_ladder() -> None:
    """The private alpha checklist should make readiness runs repeatable."""
    checklist = (ROOT / "docs" / "AEVRYN_INTERNAL_ALPHA_CHECKLIST.md").read_text(
        encoding="utf-8"
    )

    assert "Readiness Run ID" in checklist
    assert "Smoke Test" in checklist
    assert "Integration Test" in checklist
    assert "Operational Readiness Test" in checklist
    assert "Release Candidate Test" in checklist
    assert "Known Limitations" in checklist
    assert "Worker interruption is observable" in checklist
    assert "No source prose" in checklist
    assert "Can the tester continue?" in checklist


def test_internal_alpha_smoke_path_uses_v2_api_without_cli() -> None:
    """Private alpha smoke path should exercise the V2 creator workflow API."""
    repository = InMemoryProjectRepository()
    queue = InMemoryJobQueue()
    import_content_store = InMemoryImportContentStore()
    client = TestClient(
        create_app(
            authentication_service=_auth_service(repository=repository),
            project_repository=repository,
            background_job_queue=queue,
            background_job_handler=ProjectImportSnapshotHandler(
                repository=repository,
                import_content_store=import_content_store,
            ),
            import_content_store=import_content_store,
        )
    )

    registered = client.post(
        "/v2/auth/register",
        json={
            "user_id": "user_alpha",
            "email": "alpha@example.com",
            "display_name": "Alpha Tester",
            "password": PASSWORD,
            "now": NOW,
        },
    )
    assert registered.status_code == 200
    auth_headers = {
        "Authorization": f"Bearer {registered.json()['session_token']}",
        "X-Aevryn-Now": SOON,
    }

    created_project = client.post(
        "/v2/projects",
        headers=auth_headers,
        json={"project_id": "project_alpha", "name": "Alpha", "now": NOW},
    )
    assert created_project.status_code == 200
    created_story = client.post(
        "/v2/projects/project_alpha/stories",
        headers=auth_headers,
        json={"story_id": "story_alpha", "title": "Alpha Story", "now": NOW},
    )
    assert created_story.status_code == 200

    inspected = client.post(
        "/v2/imports/inspect",
        headers=auth_headers,
        json=_import_payload(),
    )
    assert inspected.status_code == 200
    assert inspected.json()["source_format"] == "txt"
    saved_import = client.post(
        "/v2/projects/project_alpha/stories/story_alpha/imports",
        headers=auth_headers,
        json={"import_id": "import_alpha", **_import_payload(), "now": NOW},
    )
    assert saved_import.status_code == 200
    submitted_run = client.post(
        "/v2/projects/project_alpha/stories/story_alpha/imports/import_alpha/runs",
        headers=auth_headers,
        json={"run_id": "run_alpha", "job_id": "job_alpha", "now": NOW},
    )
    assert submitted_run.status_code == 200
    processed = client.post(
        "/v2/workers/process",
        json={"started_at": SOON, "finished_at": SOON, "max_jobs": 1},
    )
    assert processed.status_code == 200
    assert processed.json()["succeeded_jobs"] == 1

    status = client.get("/v2/projects/project_alpha/status", headers=auth_headers)
    assert status.status_code == 200
    assert status.json()["status"] == "succeeded"
    assert status.json()["snapshots"]["available"] is True
    assert "Mark carried a brass key" not in status.text
    snapshots = client.get("/v2/projects/project_alpha/snapshots", headers=auth_headers)
    assert snapshots.status_code == 200
    assert snapshots.json()["snapshots"][0]["snapshot_kind"] == "canon"

    export_preview = client.post(
        "/v2/exports/preview",
        json={
            **_import_payload(),
            "ai_response": _ai_response(),
            "scene_id": "source_alpha_chapter_001_scene_001",
            "character_ids": ["character_mark"],
            "export_kind": "production_pack",
            "export_format": "markdown",
        },
    )
    assert export_preview.status_code == 200
    assert export_preview.json()["export_format"] == "markdown"
    assert "Mark carried a brass key" not in export_preview.json()["content"]

    baseline = run_local_v2_performance_baseline()
    benchmark_names = {item["benchmark"] for item in baseline["measurements"]}
    assert "workspace_load" in benchmark_names
    assert "validation_suite" in benchmark_names


def test_internal_alpha_worker_interruption_remains_observable_without_outputs() -> None:
    """Interrupted running workers should be honest recovery state, not fake success."""
    repository = InMemoryProjectRepository()
    queue = InMemoryJobQueue()
    import_content_store = InMemoryImportContentStore()
    client = TestClient(
        create_app(
            authentication_service=_auth_service(repository=repository),
            project_repository=repository,
            background_job_queue=queue,
            background_job_handler=ProjectImportSnapshotHandler(
                repository=repository,
                import_content_store=import_content_store,
            ),
            import_content_store=import_content_store,
        )
    )
    auth_headers = _register_alpha_user(client)
    _create_alpha_project_story_import_and_run(client, auth_headers)

    claimed_job = queue.claim_next(claimed_at=SOON)
    assert claimed_job is not None
    pending_run = repository.get_engine_run_for_worker("run_alpha")
    repository.update_engine_run(
        replace(pending_run, status="running", status_updated_at=SOON)
    )

    status = client.get("/v2/projects/project_alpha/status", headers=auth_headers)

    assert status.status_code == 200
    payload = status.json()
    assert payload["status"] == "running"
    assert payload["latest_engine_run"]["status"] == "running"
    assert payload["worker"]["state"] == "running"
    assert payload["worker"]["running_jobs"] == 1
    assert payload["snapshots"]["available"] is False
    assert payload["exports"]["available"] is False
    assert payload["latest_failure_summary"] == ""
    assert any(
        event["event_type"] == "engine_run" and event["status"] == "running"
        for event in payload["recent_workflow_events"]
    )
    assert "Mark carried a brass key" not in status.text


def _import_payload() -> dict[str, str]:
    """Return deterministic source content for the alpha smoke path."""
    return {
        "source_id": "source_alpha",
        "filename": "chapter_001.txt",
        "content_base64": base64.b64encode(
            b"Chapter 1\nMark carried a brass key."
        ).decode("ascii"),
        "title": "Alpha Source",
    }


def _ai_response() -> dict[str, object]:
    """Return deterministic accepted-candidate payload for output previews."""
    anchor_id = "source_alpha_chapter_001_scene_001_paragraph_001_sentence_001_anchor"
    return {
        "entities": [
            {
                "entity_id": "character_mark",
                "entity_type": "character",
                "display_name": "Mark",
                "evidence_anchor_id": anchor_id,
                "confidence": 0.95,
            }
        ],
        "facts": [
            {
                "fact_id": "fact_character_mark_current_item_brass_key",
                "entity_id": "character_mark",
                "attribute": "current_item",
                "value": "Brass Key",
                "evidence_anchor_id": anchor_id,
                "confidence": 0.9,
            }
        ],
        "relationships": [],
        "state_changes": [],
    }


def _register_alpha_user(client: TestClient) -> dict[str, str]:
    """Register the alpha test user and return authenticated request headers."""
    registered = client.post(
        "/v2/auth/register",
        json={
            "user_id": "user_alpha",
            "email": "alpha@example.com",
            "display_name": "Alpha Tester",
            "password": PASSWORD,
            "now": NOW,
        },
    )
    assert registered.status_code == 200
    return {
        "Authorization": f"Bearer {registered.json()['session_token']}",
        "X-Aevryn-Now": SOON,
    }


def _create_alpha_project_story_import_and_run(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """Create the saved alpha import and queued run used by recovery checks."""
    created_project = client.post(
        "/v2/projects",
        headers=auth_headers,
        json={"project_id": "project_alpha", "name": "Alpha", "now": NOW},
    )
    assert created_project.status_code == 200
    created_story = client.post(
        "/v2/projects/project_alpha/stories",
        headers=auth_headers,
        json={"story_id": "story_alpha", "title": "Alpha Story", "now": NOW},
    )
    assert created_story.status_code == 200
    saved_import = client.post(
        "/v2/projects/project_alpha/stories/story_alpha/imports",
        headers=auth_headers,
        json={"import_id": "import_alpha", **_import_payload(), "now": NOW},
    )
    assert saved_import.status_code == 200
    submitted_run = client.post(
        "/v2/projects/project_alpha/stories/story_alpha/imports/import_alpha/runs",
        headers=auth_headers,
        json={"run_id": "run_alpha", "job_id": "job_alpha", "now": NOW},
    )
    assert submitted_run.status_code == 200


def _auth_service(repository: InMemoryProjectRepository) -> AuthenticationService:
    """Return deterministic auth for the alpha smoke path."""
    return AuthenticationService(
        repository=repository,
        credential_store=InMemoryCredentialStore(),
        session_store=InMemorySessionStore(),
        password_hasher=PasswordHasher(iterations=10),
        token_factory=lambda: "token_alpha",
        config=AuthenticationConfig(session_duration_seconds=3600),
    )
