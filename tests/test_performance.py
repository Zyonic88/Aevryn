"""Tests for Phase 9 performance contracts."""

from __future__ import annotations

import base64
from collections.abc import Callable
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
    PERFORMANCE_BUDGETS,
    PerformanceMeasurement,
    build_performance_snapshot,
    compare_performance_snapshots,
    load_performance_baseline_json,
    measure_operation,
    performance_baseline_json,
    run_performance_baseline,
)
from aevryn.persistence import InMemoryProjectRepository
from aevryn.workers import InMemoryJobQueue
from aevryn.workers.models import BackgroundJob

ROOT = Path(__file__).resolve().parents[1]
NOW = "2026-06-27T00:00:00Z"
SOON = "2026-06-27T00:30:00Z"


def test_phase9_performance_docs_define_budgets_and_boundaries() -> None:
    """Phase 9 must define budgets, latency scope, and regression boundaries."""
    performance_doc = (ROOT / "docs" / "AEVRYN_PERFORMANCE.md").read_text(
        encoding="utf-8"
    )
    acceptance_doc = (
        ROOT / "docs" / "AEVRYN_V2_PHASE_9_ACCEPTANCE.md"
    ).read_text(encoding="utf-8")

    assert "Performance budgets define what acceptable means." in performance_doc
    assert "Phase 9 optimizes latency" in performance_doc
    assert "Throughput and scalability belong after" in performance_doc
    assert "Performance snapshots are metadata-only." in acceptance_doc
    assert "Regression checks tolerate small variance" in acceptance_doc


def test_phase9_latency_budgets_classify_thresholds() -> None:
    """Latency budgets should classify target, warning, and critical ranges."""
    import_budget = PERFORMANCE_BUDGETS["import_inspect"]
    project_status_budget = PERFORMANCE_BUDGETS["project_status"]

    assert import_budget.classify(145.0) == "target"
    assert import_budget.classify(300.0) == "acceptable"
    assert import_budget.classify(750.0) == "warning"
    assert import_budget.classify(1000.0) == "critical"
    assert project_status_budget.classify(42.0) == "target"
    assert project_status_budget.classify(500.0) == "critical"


def test_phase9_measured_only_budgets_do_not_fake_slas() -> None:
    """Measured-only areas should not fabricate warning or critical states."""
    assert PERFORMANCE_BUDGETS["worker_processing"].classify(10_000.0) == "measured"
    assert PERFORMANCE_BUDGETS["validation_suite"].classify(8_300.0) == "measured"
    assert PERFORMANCE_BUDGETS["snapshot_creation"].classify(750.0) == "measured"


def test_performance_snapshot_is_stable_metadata_only() -> None:
    """Performance snapshots should contain stable budget metadata only."""
    snapshot = build_performance_snapshot(
        [
            PerformanceMeasurement(benchmark="workspace_load", elapsed_ms=620.4444),
            PerformanceMeasurement(benchmark="project_status", elapsed_ms=42.12),
        ]
    )

    assert snapshot == {
        "schema_version": 1,
        "measurements": [
            {
                "benchmark": "project_status",
                "elapsed_ms": 42.12,
                "status": "target",
            },
            {
                "benchmark": "workspace_load",
                "elapsed_ms": 620.444,
                "status": "target",
            },
        ],
    }
    assert "created_at" not in snapshot
    assert "source_text" not in snapshot
    assert "path" not in snapshot


def test_performance_snapshot_rejects_duplicate_benchmarks() -> None:
    """Snapshot construction should reject ambiguous duplicate measurements."""
    try:
        build_performance_snapshot(
            [
                PerformanceMeasurement(benchmark="project_status", elapsed_ms=42.0),
                PerformanceMeasurement(benchmark="project_status", elapsed_ms=43.0),
            ]
        )
    except ValueError as error:
        assert str(error) == "Performance measurement benchmarks must be unique."
    else:
        raise AssertionError("Expected duplicate performance measurements to fail.")


def test_performance_baseline_json_is_stable_metadata_only() -> None:
    """Baseline artifacts should serialize stable metadata without local context."""
    snapshot = build_performance_snapshot(
        [
            PerformanceMeasurement(benchmark="project_status", elapsed_ms=42.12),
            PerformanceMeasurement(benchmark="import_inspect", elapsed_ms=145.0),
        ]
    )

    baseline_text = performance_baseline_json(snapshot)

    assert baseline_text == (
        "{\n"
        '  "artifact_kind": "aevryn_phase9_performance_baseline",\n'
        '  "schema_version": 1,\n'
        '  "snapshot": {\n'
        '    "measurements": [\n'
        "      {\n"
        '        "benchmark": "import_inspect",\n'
        '        "elapsed_ms": 145.0,\n'
        '        "status": "target"\n'
        "      },\n"
        "      {\n"
        '        "benchmark": "project_status",\n'
        '        "elapsed_ms": 42.12,\n'
        '        "status": "target"\n'
        "      }\n"
        "    ],\n"
        '    "schema_version": 1\n'
        "  }\n"
        "}\n"
    )
    assert load_performance_baseline_json(baseline_text) == snapshot
    assert "Mark carried a rusty dagger" not in baseline_text
    assert "created_at" not in baseline_text
    assert "C:\\" not in baseline_text


def test_performance_baseline_json_rejects_tampered_status() -> None:
    """Baseline artifacts should reject statuses that do not match budgets."""
    tampered = (
        "{\n"
        '  "artifact_kind": "aevryn_phase9_performance_baseline",\n'
        '  "schema_version": 1,\n'
        '  "snapshot": {\n'
        '    "schema_version": 1,\n'
        '    "measurements": [\n'
        "      {\n"
        '        "benchmark": "project_status",\n'
        '        "elapsed_ms": 900.0,\n'
        '        "status": "target"\n'
        "      }\n"
        "    ]\n"
        "  }\n"
        "}\n"
    )

    try:
        load_performance_baseline_json(tampered)
    except ValueError as error:
        assert str(error) == "Performance measurement status does not match budget."
    else:
        raise AssertionError("Expected invalid performance baseline to fail.")


def test_generated_performance_baselines_are_ignored_by_default() -> None:
    """Local measured baseline artifacts should not be committed accidentally."""
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")

    assert "performance-baselines/" in gitignore


def test_measure_operation_returns_value_and_metadata_only_timing() -> None:
    """Operation timing should not inspect or serialize the operation result."""
    ticks = iter((10.0, 10.145))

    value, measurement = measure_operation(
        benchmark="import_inspect",
        operation=lambda: {"source_text": "Mark carried a rusty dagger."},
        timer=lambda: next(ticks),
    )

    assert value == {"source_text": "Mark carried a rusty dagger."}
    assert measurement == PerformanceMeasurement(
        benchmark="import_inspect",
        elapsed_ms=145.0,
    )


def test_run_performance_baseline_measures_real_v2_boundaries() -> None:
    """Phase 9 baseline should measure V2 boundaries without storing payloads."""
    client = _phase9_client()
    _register_user(client)
    _create_project_and_story(client)
    timer = _deterministic_timer(step_seconds=0.01)

    snapshot = run_performance_baseline(
        {
            "import_inspect": lambda: _assert_ok(
                client.post("/v2/imports/inspect", json=_inspect_payload())
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
        },
        timer=timer,
    )

    assert snapshot == {
        "schema_version": 1,
        "measurements": [
            {"benchmark": "export_preview", "elapsed_ms": 10.0, "status": "target"},
            {"benchmark": "import_inspect", "elapsed_ms": 10.0, "status": "target"},
            {"benchmark": "import_save", "elapsed_ms": 10.0, "status": "target"},
            {"benchmark": "project_status", "elapsed_ms": 10.0, "status": "target"},
            {"benchmark": "snapshot_creation", "elapsed_ms": 10.0, "status": "measured"},
            {"benchmark": "worker_processing", "elapsed_ms": 10.0, "status": "measured"},
            {"benchmark": "workspace_load", "elapsed_ms": 10.0, "status": "target"},
        ],
    }
    assert "Mark carried a rusty dagger" not in str(snapshot)
    assert "serialized_output" not in str(snapshot)
    assert "session_token" not in str(snapshot)


def test_compare_performance_snapshots_tolerates_small_variance() -> None:
    """Small timing variance should not be reported as a regression."""
    previous = build_performance_snapshot(
        [PerformanceMeasurement(benchmark="import_inspect", elapsed_ms=145.0)]
    )
    current = build_performance_snapshot(
        [PerformanceMeasurement(benchmark="import_inspect", elapsed_ms=148.0)]
    )

    assert compare_performance_snapshots(previous=previous, current=current) == []


def test_compare_performance_snapshots_flags_major_slowdowns() -> None:
    """Large slowdowns should be reported with stable regression metadata."""
    previous = build_performance_snapshot(
        [PerformanceMeasurement(benchmark="import_inspect", elapsed_ms=145.0)]
    )
    current = build_performance_snapshot(
        [PerformanceMeasurement(benchmark="import_inspect", elapsed_ms=920.0)]
    )

    assert compare_performance_snapshots(previous=previous, current=current) == [
        {
            "benchmark": "import_inspect",
            "previous_ms": 145.0,
            "current_ms": 920.0,
            "delta_ms": 775.0,
            "ratio": 6.345,
            "status": "critical",
        }
    ]


def test_compare_performance_snapshots_validates_inputs() -> None:
    """Snapshot comparisons should reject malformed direct-call payloads."""
    previous = build_performance_snapshot(
        [PerformanceMeasurement(benchmark="project_status", elapsed_ms=42.0)]
    )
    current = {
        "schema_version": 1,
        "measurements": [
            {"benchmark": "project_status", "elapsed_ms": 500.0, "status": "target"}
        ],
    }

    try:
        compare_performance_snapshots(previous=previous, current=current)  # type: ignore[arg-type]
    except ValueError as error:
        assert str(error) == "Performance measurement status does not match budget."
    else:
        raise AssertionError("Expected malformed performance snapshot to fail.")


def _phase9_client() -> TestClient:
    """Return a test client wired for Phase 9 workflow measurement."""
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
    """Create the deterministic Phase 9 test user."""
    response = client.post(
        "/v2/auth/register",
        json={
            "user_id": "user_demo",
            "email": "demo@example.com",
            "display_name": "Demo User",
            "password": "StrongPass123",
            "now": NOW,
        },
    )
    assert response.status_code == 200


def _create_project_and_story(client: TestClient) -> None:
    """Create deterministic project and story parents."""
    project = client.post(
        "/v2/projects",
        headers=_auth_headers(),
        json={"project_id": "project_alpha", "name": "Alpha", "now": NOW},
    )
    story = client.post(
        "/v2/projects/project_alpha/stories",
        headers=_auth_headers(),
        json={"story_id": "story_alpha", "title": "Alpha Story", "now": NOW},
    )
    assert project.status_code == 200
    assert story.status_code == 200


def _process_worker_job(client: TestClient) -> object:
    """Submit and process one import job."""
    submitted = client.post(
        "/v2/projects/project_alpha/stories/story_alpha/imports/import_alpha/runs",
        headers=_auth_headers(),
        json={"run_id": "run_alpha", "job_id": "job_alpha", "now": NOW},
    )
    assert submitted.status_code == 200
    return _assert_ok(
        client.post(
            "/v2/workers/process",
            json={"started_at": SOON, "finished_at": SOON, "max_jobs": 1},
        )
    )


def _load_workspace_shell(client: TestClient) -> object:
    """Load project shell metadata and backend-provided status."""
    return {
        "project": _assert_ok(
            client.get("/v2/projects/project_alpha", headers=_auth_headers())
        ),
        "status": _assert_ok(
            client.get("/v2/projects/project_alpha/status", headers=_auth_headers())
        ),
    }


def _assert_ok(response: Any) -> object:
    """Assert a TestClient response is successful and return its JSON payload."""
    assert response.status_code == 200
    return response.json()


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


def _deterministic_timer(step_seconds: float) -> Callable[[], float]:
    """Return a deterministic increasing timer."""
    elapsed = 0.0

    def timer() -> float:
        nonlocal elapsed
        value = elapsed
        elapsed += step_seconds
        return value

    return timer


class _RecordingWorkerHandler:
    """Worker handler that accepts queued jobs for performance boundary tests."""

    def process(self, _job: BackgroundJob) -> None:
        """Accept one queued background job."""
