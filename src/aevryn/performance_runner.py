"""Local Phase 9 performance baseline runner."""

from __future__ import annotations

import base64
import json
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any

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
from aevryn.performance import (
    PerformanceRegressionPayload,
    PerformanceSnapshotPayload,
    compare_performance_snapshots,
    load_performance_baseline_json,
    performance_baseline_json,
    run_performance_baseline,
)
from aevryn.persistence import InMemoryProjectRepository
from aevryn.validation import ValidationRunner
from aevryn.workers import InMemoryJobQueue
from aevryn.workers.models import BackgroundJob

NOW = "2026-06-27T00:00:00Z"
SOON = "2026-06-27T00:30:00Z"


def run_local_v2_performance_baseline() -> PerformanceSnapshotPayload:
    """Measure the local in-memory V2 workflow path."""
    client = _baseline_client()
    _register_user(client)
    _create_project_and_story(client)
    with tempfile.TemporaryDirectory(prefix="aevryn_phase9_validation_") as temp_dir:
        validation_case_dir, validation_source_root = _prepare_validation_fixture(
            Path(temp_dir)
        )
        return run_performance_baseline(
            {
                "import_inspect": lambda: _assert_ok(
                    client.post(
                        "/v2/imports/inspect",
                        headers=_auth_headers(),
                        json=_inspect_payload(),
                    )
                ),
                "import_save": lambda: _assert_ok(
                    client.post(
                        "/v2/projects/project_alpha/stories/story_alpha/imports",
                        headers=_auth_headers(),
                        json=_import_create_payload(),
                    )
                ),
                "worker_processing": lambda: _process_worker_job(client),
                "snapshot_creation": lambda: _assert_ok(
                    client.post(
                        "/v2/workers/runs/run_alpha/snapshots",
                        json={
                            "snapshot_id": "snapshot_alpha",
                            "snapshot_kind": "canon",
                            "content_type": "application/json",
                            "serialized_output": "{}",
                            "now": SOON,
                        },
                    )
                ),
                "project_status": lambda: _assert_ok(
                    client.get(
                        "/v2/projects/project_alpha/status",
                        headers=_auth_headers(),
                    )
                ),
                "workspace_load": lambda: _load_workspace_shell(client),
                "export_preview": lambda: _assert_ok(
                    client.post("/v2/exports/preview", json=_export_preview_payload())
                ),
                "validation_suite": lambda: _run_validation_suite(
                    case_dir=validation_case_dir,
                    source_root=validation_source_root,
                )
            }
        )


def write_local_v2_performance_baseline(output_path: Path) -> Path:
    """Write a local metadata-only V2 performance baseline artifact."""
    if output_path.exists() and output_path.is_dir():
        raise ValueError(f"Performance baseline path must be a file: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot = run_local_v2_performance_baseline()
    output_path.write_text(performance_baseline_json(snapshot), encoding="utf-8")
    return output_path


def compare_local_v2_performance_baseline(
    previous_path: Path,
) -> list[PerformanceRegressionPayload]:
    """Compare a previous baseline artifact against a new local run."""
    previous = load_performance_baseline_json(previous_path.read_text(encoding="utf-8"))
    current = run_local_v2_performance_baseline()
    return compare_performance_snapshots(previous=previous, current=current)


def _baseline_client() -> TestClient:
    """Return a local in-memory API client for baseline measurement."""
    repository = InMemoryProjectRepository()
    return TestClient(
        create_app(
            authentication_service=_auth_service(repository=repository),
            project_repository=repository,
            background_job_queue=InMemoryJobQueue(),
            background_job_handler=_RecordingWorkerHandler(),
            import_content_store=InMemoryImportContentStore(),
        )
    )


def _register_user(client: TestClient) -> None:
    """Create the deterministic baseline user."""
    _assert_ok(
        client.post(
            "/v2/auth/register",
            json={
                "user_id": "user_demo",
                "email": "demo@example.com",
                "display_name": "Demo User",
                "password": "StrongPass123",
                "now": NOW,
            },
        )
    )


def _create_project_and_story(client: TestClient) -> None:
    """Create deterministic baseline project and story parents."""
    _assert_ok(
        client.post(
            "/v2/projects",
            headers=_auth_headers(),
            json={"project_id": "project_alpha", "name": "Alpha", "now": NOW},
        )
    )
    _assert_ok(
        client.post(
            "/v2/projects/project_alpha/stories",
            headers=_auth_headers(),
            json={"story_id": "story_alpha", "title": "Alpha Story", "now": NOW},
        )
    )


def _process_worker_job(client: TestClient) -> object:
    """Submit and process one baseline worker job."""
    _assert_ok(
        client.post(
            "/v2/projects/project_alpha/stories/story_alpha/imports/import_alpha/runs",
            headers=_auth_headers(),
            json={"run_id": "run_alpha", "job_id": "job_alpha", "now": NOW},
        )
    )
    return _assert_ok(
        client.post(
            "/v2/workers/process",
            json={"started_at": SOON, "finished_at": SOON, "max_jobs": 1},
        )
    )


def _load_workspace_shell(client: TestClient) -> object:
    """Load read-only metadata needed by the project workspace shell."""
    return {
        "project": _assert_ok(
            client.get("/v2/projects/project_alpha", headers=_auth_headers())
        ),
        "status": _assert_ok(
            client.get("/v2/projects/project_alpha/status", headers=_auth_headers())
        ),
    }


def _prepare_validation_fixture(root: Path) -> tuple[Path, Path]:
    """Create a tiny deterministic validation fixture outside timed measurement."""
    source_root = root / "sources"
    source_dir = source_root / "Phase 9"
    case_dir = root / "cases"
    source_dir.mkdir(parents=True, exist_ok=True)
    case_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "Chapter 1.txt").write_text(
        "Chapter 1\nMark found a brass key.",
        encoding="utf-8",
    )
    (source_dir / "Chapter 2.txt").write_text(
        "Chapter 2\nMark opened the archive.",
        encoding="utf-8",
    )
    case_path = case_dir / "phase9_validation_case.json"
    _write_validation_case(
        case_path,
        expected_import={
            "chapter_files": 1,
            "source_manifest_digest": "0" * 64,
            "chapters": 1,
            "scenes": 1,
            "paragraphs": 1,
            "sentences": 1,
            "evidence_anchors": 1,
            "import_digest": "0" * 64,
        },
        expected_extraction={
            "scene_inputs": 1,
            "evidence_anchors": 1,
            "extraction_input_digest": "0" * 64,
            "extraction_prompt_digest": "0" * 64,
        },
    )
    calibration = ValidationRunner(case_dir=case_dir, source_root=source_root).run()
    result = calibration.results[0]
    if result.actual_import is None or result.actual_extraction is None:
        raise ValueError("Validation baseline fixture did not produce metrics.")
    _write_validation_case(
        case_path,
        expected_import=asdict(result.actual_import),
        expected_extraction=asdict(result.actual_extraction),
    )
    return case_dir, source_root


def _write_validation_case(
    case_path: Path,
    *,
    expected_import: dict[str, object],
    expected_extraction: dict[str, object],
) -> None:
    """Write one deterministic validation case definition."""
    case_path.write_text(
        json.dumps(
            {
                "case_id": "phase9_validation_case",
                "title": "Phase 9 Baseline",
                "genre": "Performance",
                "source_directory": "Phase 9",
                "chapter_glob": "*.txt",
                "expected_import": expected_import,
                "expected_extraction": expected_extraction,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _run_validation_suite(*, case_dir: Path, source_root: Path) -> object:
    """Run the tiny validation suite and return metadata only."""
    result = ValidationRunner(case_dir=case_dir, source_root=source_root).run()
    if not result.passed:
        raise ValueError("Validation baseline fixture failed.")
    return {
        "cases": result.totals.cases,
        "score": result.score,
        "suite_digest": result.suite_digest,
    }


def _inspect_payload() -> dict[str, str]:
    """Return a deterministic import inspect payload."""
    return {
        "source_id": "source_alpha",
        "filename": "chapter_001.txt",
        "content_base64": _b64("Chapter 1\nMark carried a rusty dagger."),
        "title": "Alpha Source",
    }


def _import_create_payload() -> dict[str, str]:
    """Return a deterministic import create payload."""
    return {
        "import_id": "import_alpha",
        **_inspect_payload(),
        "now": NOW,
    }


def _export_preview_payload() -> dict[str, object]:
    """Return a deterministic export preview payload."""
    anchor_id = "source_alpha_chapter_001_scene_001_paragraph_001_sentence_001_anchor"
    return {
        "source_id": "source_alpha",
        "filename": "chapter_001.txt",
        "content_base64": _b64("Chapter 1\nMark carried a rusty dagger."),
        "ai_response": {
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
                    "fact_id": "fact_character_mark_current_weapon_rusty_dagger",
                    "entity_id": "character_mark",
                    "attribute": "current_weapon",
                    "value": "Rusty Dagger",
                    "evidence_anchor_id": anchor_id,
                    "confidence": 0.9,
                }
            ],
            "relationships": [],
            "state_changes": [],
        },
        "scene_id": "source_alpha_chapter_001_scene_001",
        "character_ids": ["character_mark"],
        "export_kind": "production_pack",
        "export_format": "markdown",
    }


def _assert_ok(response: Any) -> object:
    """Assert an API response succeeded and return JSON payload."""
    if response.status_code != 200:
        raise ValueError(f"Baseline request failed: {response.status_code} {response.text}")
    return response.json()


def _b64(value: str) -> str:
    """Return base64-encoded UTF-8 text."""
    return base64.b64encode(value.encode("utf-8")).decode("ascii")


def _auth_headers() -> dict[str, str]:
    """Return deterministic auth headers."""
    return {"Authorization": "Bearer token_001", "X-Aevryn-Now": SOON}


def _auth_service(repository: InMemoryProjectRepository) -> AuthenticationService:
    """Return a deterministic authentication service."""
    return AuthenticationService(
        repository=repository,
        credential_store=InMemoryCredentialStore(),
        session_store=InMemorySessionStore(),
        password_hasher=PasswordHasher(iterations=10),
        token_factory=lambda: "token_001",
        config=AuthenticationConfig(session_duration_seconds=3600),
    )


class _RecordingWorkerHandler:
    """Worker handler that accepts queued jobs for baseline measurement."""

    def process(self, _job: BackgroundJob) -> None:
        """Accept one queued background job."""
