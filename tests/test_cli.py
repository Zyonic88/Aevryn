"""Tests for the Aevryn command line interface."""

import json
import os
import re
import shutil
import urllib.error
import urllib.request
from io import BytesIO
from pathlib import Path
from typing import Any, cast

import pytest
from pytest import CaptureFixture, MonkeyPatch

from aevryn.cli import (
    _run_audit_access_report,
    _run_audit_access_verify,
    _run_audit_ledger_verify,
    _run_observability_config_check,
    _run_production_config_check,
    _run_provider_config_check,
    main,
)
from aevryn.importing import StoryImporter
from aevryn.validation.runner import (
    _extraction_input_digest,
    _extraction_prompt_digest,
    _source_manifest_digest,
    _structure_digest,
)


def source_file() -> Path:
    """Create a small source file for CLI tests."""
    path = Path("build") / "test_cli" / "chapter.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "Chapter 1",
                "Mark carried a rusty dagger.",
                "",
                "Chapter 2",
                "Mark bought an iron sword.",
            ]
        ),
        encoding="utf-8",
    )
    return path


def single_scene_source_file() -> Path:
    """Create a one-scene source file for AI JSON CLI tests."""
    path = Path("build") / "test_cli" / "single_scene.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "Chapter 1",
                "Mark bought an iron sword.",
            ]
        ),
        encoding="utf-8",
    )
    return path


def unicode_source_file() -> Path:
    """Create a source file containing multilingual punctuation."""
    path = Path("build") / "test_cli" / "unicode_scene.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "Chapter 1",
                "Lin saw 【Entry】 shimmer beside his fiancée.",
            ]
        ),
        encoding="utf-8",
    )
    return path


def two_scene_source_file() -> Path:
    """Create a one-chapter, two-scene source file for scene-position CLI tests."""
    path = Path("build") / "test_cli" / "two_scene.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "Chapter 1",
                "Mark was calm in the quiet hangar.",
                "",
                "---",
                "",
                "Mark became alarmed as the hangar alarm started.",
            ]
        ),
        encoding="utf-8",
    )
    return path


def out_of_order_source_file() -> Path:
    """Create a source file with explicit chapters in the wrong order."""
    path = Path("build") / "test_cli" / "out_of_order.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "Chapter 3",
                "Third chapter text.",
                "",
                "Chapter 1",
                "First chapter text.",
            ]
        ),
        encoding="utf-8",
    )
    return path


def test_cli_help_shows_v1_workflow(capsys: CaptureFixture[str]) -> None:
    """Top-level CLI help should guide a first user through the V1 flow."""
    with pytest.raises(SystemExit) as error:
        main(["--help"])
    output = capsys.readouterr().out

    assert error.value.code == 0
    assert "Aevryn V1 proof CLI" in output
    assert "Typical V1 flow:" in output
    assert "aevryn import chapter_001.txt --source-id my_story" in output
    assert "aevryn validate --summary-only --snapshot-dir snapshots/run_name" in output
    assert "aevryn api --host 127.0.0.1 --port 8000" in output


def test_cli_help_describes_current_command_purpose(
    capsys: CaptureFixture[str],
) -> None:
    """Top-level CLI help should describe commands in current V1 terms."""
    with pytest.raises(SystemExit) as error:
        main(["--help"])
    output = capsys.readouterr().out

    assert error.value.code == 0
    assert "Inspect how source text is parsed" in output
    assert "Apply evidence-bounded AI JSON candidates through" in output
    assert "Canon Updating." in output
    assert "Print a canon-backed production prompt pack" in output
    assert "Run the local validation corpus and optional" in output
    assert "deterministic snapshot." in output


def test_import_help_describes_source_arguments(capsys: CaptureFixture[str]) -> None:
    """Import help should explain the source identifiers a user must choose."""
    with pytest.raises(SystemExit) as error:
        main(["import", "--help"])
    output = capsys.readouterr().out

    assert error.value.code == 0
    assert "Path to a supported source file" in output
    for source_format in ("TXT", "Markdown", "HTML", "FB2", "DOCX", "ODT", "EPUB"):
        assert source_format in output
    assert "Stable machine ID for this imported source." in output
    assert "Human-readable source title" in output


def test_character_help_describes_presentation_and_machine_outputs(
    capsys: CaptureFixture[str],
) -> None:
    """Character help should explain markdown versus JSON and CSV outputs."""
    with pytest.raises(SystemExit) as error:
        main(["character", "--help"])
    output = capsys.readouterr().out

    assert error.value.code == 0
    assert "Markdown is presentation-first" in output
    assert "JSON/CSV preserve machine detail." in output
    assert "character_mark" in output
    assert "accepted_entity_ids" in output
    assert "(default: markdown)" in output


def test_scene_help_describes_timeline_safe_arguments(
    capsys: CaptureFixture[str],
) -> None:
    """Scene help should surface timeline-safe scene and extractor options."""
    with pytest.raises(SystemExit) as error:
        main(["scene", "--help"])
    output = capsys.readouterr().out

    assert error.value.code == 0
    assert "Scene ID to inspect" in output
    assert "Repeat for multiple" in output
    assert "characters." in output
    assert "Evidence-bounded AI JSON response" in output
    assert "Markdown is presentation-first" in output
    assert "preserves machine detail." in output


def test_validate_help_describes_snapshot_and_source_root(
    capsys: CaptureFixture[str],
) -> None:
    """Validate help should make corpus source and snapshot behavior discoverable."""
    with pytest.raises(SystemExit) as error:
        main(["validate", "--help"])
    output = capsys.readouterr().out

    assert error.value.code == 0
    assert "Directory containing validation case metadata JSON" in output
    assert "files." in output
    assert "Root directory containing local validation chapter" in output
    assert "folders. Overrides AEVRYN_VALIDATION_ROOT." in output
    assert "List validation cases without importing source files." in output
    assert "deterministic snapshot" in output
    assert "metadata is written." in output
    assert "Text is scan-friendly" in output
    assert "JSON preserves" in output
    assert "machine detail." in output


def test_world_help_describes_presentation_and_machine_outputs(
    capsys: CaptureFixture[str],
) -> None:
    """World help should explain markdown versus JSON outputs."""
    with pytest.raises(SystemExit) as error:
        main(["world", "--help"])
    output = capsys.readouterr().out

    assert error.value.code == 0
    assert "Markdown is presentation-first" in output
    assert "preserves machine detail." in output


def test_api_help_describes_server_options(capsys: CaptureFixture[str]) -> None:
    """API help should describe local platform server options."""
    with pytest.raises(SystemExit) as error:
        main(["api", "--help"])
    output = capsys.readouterr().out

    assert error.value.code == 0
    assert "Run the V2 Backend API" in output
    assert "--allowed-origin" in output
    assert "--reload" in output


def test_provider_smoke_help_describes_synthetic_workflow(
    capsys: CaptureFixture[str],
) -> None:
    """Provider smoke help should describe the local synthetic workflow."""
    with pytest.raises(SystemExit) as error:
        main(["provider-smoke", "--help"])
    output = capsys.readouterr().out

    assert error.value.code == 0
    assert "synthetic provider-backed API workflow smoke test" in output
    assert "--env-file" in output
    assert "--timeout-seconds" in output


def test_provider_smoke_requires_local_env_file(
    tmp_path: Path,
    capsys: CaptureFixture[str],
) -> None:
    """Provider smoke should fail before any provider call when env is missing."""
    exit_code = main(["provider-smoke", "--env-file", str(tmp_path / "missing.env")])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Local env file does not exist" in captured.err


def test_provider_smoke_reads_env_file_without_printing_key(
    tmp_path: Path,
    capsys: CaptureFixture[str],
    monkeypatch: MonkeyPatch,
) -> None:
    """Provider smoke should print metadata only and never echo the API key."""
    env_file = tmp_path / ".env.aevryn.local"
    env_file.write_text(
        "\n".join(
            (
                "AEVRYN_OPENAI_API_KEY=secret-provider-key",
                "AEVRYN_OPENAI_MODEL=test-model",
            )
        ),
        encoding="utf-8",
    )

    def fake_smoke(
        *,
        api_key: str,
        model: str,
        timeout_seconds: float,
    ) -> dict[str, object]:
        assert api_key == "secret-provider-key"
        assert model == "test-model"
        assert timeout_seconds == 12.5
        return {"model": model, "ok": "provider_api_workflow_synthetic_completed"}

    monkeypatch.setattr("aevryn.cli._run_provider_api_workflow_smoke", fake_smoke)

    exit_code = main(
        [
            "provider-smoke",
            "--env-file",
            str(env_file),
            "--timeout-seconds",
            "12.5",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "model=test-model" in captured.out
    assert "ok=provider_api_workflow_synthetic_completed" in captured.out
    assert "secret-provider-key" not in captured.out
    assert "secret-provider-key" not in captured.err


def test_provider_config_check_help_describes_provider_review_boundary(
    capsys: CaptureFixture[str],
) -> None:
    """Provider config check help should not imply public-beta approval."""
    with pytest.raises(SystemExit) as error:
        main(["provider-config-check", "--help"])
    output = capsys.readouterr().out

    assert error.value.code == 0
    assert "provider extraction configuration" in output
    assert "does not approve provider use for public beta" in output


def test_provider_config_check_reports_metadata_only_contract(
    capsys: CaptureFixture[str],
    monkeypatch: MonkeyPatch,
) -> None:
    """Provider config check should print provider metadata and no keys."""
    env_values = {
        "AEVRYN_DEPLOYMENT_ENV": "production",
        "AEVRYN_EXTRACTION_MODE": "openai",
        "AEVRYN_OPENAI_API_KEY": "secret-openai-key",
        "AEVRYN_OPENAI_MODEL": "gpt-5.4-mini",
        "AEVRYN_OPENAI_TIMEOUT_SECONDS": "90",
        "AEVRYN_OPENAI_MAX_RESPONSE_BYTES": "1048576",
    }
    for key, value in env_values.items():
        monkeypatch.setenv(key, value)

    exit_code = main(["provider-config-check"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "deployment_env=production" in captured.out
    assert "provider=openai" in captured.out
    assert "extraction_mode=openai" in captured.out
    assert "model=gpt-5.4-mini" in captured.out
    assert "timeout_seconds=90.0" in captured.out
    assert "max_response_bytes=1048576" in captured.out
    assert "request_storage=disabled" in captured.out
    assert "responses_store=false" in captured.out
    assert "provider_review=required" in captured.out
    assert "public_beta=blocked_until_provider_review" in captured.out
    assert "secrets_printed=0" in captured.out
    assert "ok=provider_config_contract_checked" in captured.out
    assert "secret-openai-key" not in captured.out
    assert "secret-openai-key" not in captured.err


def test_provider_config_check_rejects_demo_mode() -> None:
    """Production provider config should reject demo extraction mode."""
    with pytest.raises(ValueError, match="AEVRYN_EXTRACTION_MODE=openai"):
        _run_provider_config_check(
            {
                "AEVRYN_DEPLOYMENT_ENV": "production",
                "AEVRYN_EXTRACTION_MODE": "demo",
                "AEVRYN_OPENAI_API_KEY": "secret-openai-key",
                "AEVRYN_OPENAI_MODEL": "gpt-5.4-mini",
                "AEVRYN_OPENAI_TIMEOUT_SECONDS": "90",
                "AEVRYN_OPENAI_MAX_RESPONSE_BYTES": "1048576",
            }
        )


def test_provider_config_check_requires_provider_key_without_printing_it() -> None:
    """Provider config should fail before use when the key is absent."""
    with pytest.raises(ValueError, match="AEVRYN_OPENAI_API_KEY") as error:
        _run_provider_config_check(
            {
                "AEVRYN_DEPLOYMENT_ENV": "production",
                "AEVRYN_EXTRACTION_MODE": "openai",
                "AEVRYN_OPENAI_MODEL": "gpt-5.4-mini",
                "AEVRYN_OPENAI_TIMEOUT_SECONDS": "90",
                "AEVRYN_OPENAI_MAX_RESPONSE_BYTES": "1048576",
            }
        )
    assert "secret" not in str(error.value).lower()


def test_provider_config_check_rejects_invalid_provider_bounds() -> None:
    """Provider timeout and response-size limits should fail closed."""
    with pytest.raises(ValueError, match="AEVRYN_OPENAI_TIMEOUT_SECONDS"):
        _run_provider_config_check(
            {
                "AEVRYN_DEPLOYMENT_ENV": "production",
                "AEVRYN_EXTRACTION_MODE": "openai",
                "AEVRYN_OPENAI_API_KEY": "secret-openai-key",
                "AEVRYN_OPENAI_MODEL": "gpt-5.4-mini",
                "AEVRYN_OPENAI_TIMEOUT_SECONDS": "0",
                "AEVRYN_OPENAI_MAX_RESPONSE_BYTES": "1048576",
            }
        )

    with pytest.raises(ValueError, match="AEVRYN_OPENAI_MAX_RESPONSE_BYTES"):
        _run_provider_config_check(
            {
                "AEVRYN_DEPLOYMENT_ENV": "production",
                "AEVRYN_EXTRACTION_MODE": "openai",
                "AEVRYN_OPENAI_API_KEY": "secret-openai-key",
                "AEVRYN_OPENAI_MODEL": "gpt-5.4-mini",
                "AEVRYN_OPENAI_TIMEOUT_SECONDS": "90",
                "AEVRYN_OPENAI_MAX_RESPONSE_BYTES": "-1",
            }
        )


def test_project_db_smoke_help_describes_postgresql_smoke(
    capsys: CaptureFixture[str],
) -> None:
    """Project database smoke help should describe the metadata-only DB check."""
    with pytest.raises(SystemExit) as error:
        main(["project-db-smoke", "--help"])
    output = capsys.readouterr().out

    assert error.value.code == 0
    assert "metadata-only PostgreSQL Project Database smoke test" in output
    assert "--database-url-env" in output
    assert "--no-bootstrap" in output


def test_project_db_smoke_requires_process_env(
    capsys: CaptureFixture[str],
    monkeypatch: MonkeyPatch,
) -> None:
    """Project database smoke should fail before connecting when env is missing."""
    monkeypatch.delenv("AEVRYN_PROJECT_DATABASE_URL", raising=False)

    exit_code = main(["project-db-smoke"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "AEVRYN_PROJECT_DATABASE_URL is required" in captured.err


def test_project_db_smoke_reads_env_without_printing_url(
    capsys: CaptureFixture[str],
    monkeypatch: MonkeyPatch,
) -> None:
    """Project database smoke should print metadata only and never echo the DB URL."""
    database_url = "postgresql://aevryn_app:secret-db-password@localhost:5432/aevryn_dev"
    monkeypatch.setenv("AEVRYN_PROJECT_DATABASE_URL", database_url)

    def fake_smoke(
        *,
        database_url: str,
        bootstrap_schema: bool = True,
    ) -> dict[str, object]:
        assert database_url == (
            "postgresql://aevryn_app:secret-db-password@localhost:5432/aevryn_dev"
        )
        assert bootstrap_schema is True
        return {
            "adapter": "postgresql",
            "schema": "bootstrapped",
            "ok": "project_database_postgresql_smoke_completed",
        }

    monkeypatch.setattr("aevryn.cli._run_project_database_smoke", fake_smoke)

    exit_code = main(["project-db-smoke"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "adapter=postgresql" in captured.out
    assert "schema=bootstrapped" in captured.out
    assert "ok=project_database_postgresql_smoke_completed" in captured.out
    assert "secret-db-password" not in captured.out
    assert "secret-db-password" not in captured.err
    assert database_url not in captured.out
    assert database_url not in captured.err


def test_project_db_smoke_can_validate_existing_schema_without_bootstrap(
    capsys: CaptureFixture[str],
    monkeypatch: MonkeyPatch,
) -> None:
    """Production runtime smoke checks should be able to avoid DDL."""
    database_url = "postgresql://aevryn_app:secret-db-password@localhost:5432/aevryn_dev"
    monkeypatch.setenv("AEVRYN_PROJECT_DATABASE_URL", database_url)

    def fake_smoke(
        *,
        database_url: str,
        bootstrap_schema: bool = True,
    ) -> dict[str, object]:
        assert database_url.endswith("/aevryn_dev")
        assert bootstrap_schema is False
        return {
            "adapter": "postgresql",
            "schema": "existing",
            "ok": "project_database_postgresql_smoke_completed",
        }

    monkeypatch.setattr("aevryn.cli._run_project_database_smoke", fake_smoke)

    exit_code = main(["project-db-smoke", "--no-bootstrap"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "schema=existing" in captured.out
    assert "ok=project_database_postgresql_smoke_completed" in captured.out
    assert "secret-db-password" not in captured.out
    assert "secret-db-password" not in captured.err


def test_storage_smoke_help_describes_r2_storage_check(
    capsys: CaptureFixture[str],
) -> None:
    """Storage smoke help should describe the metadata-only R2 check."""
    with pytest.raises(SystemExit) as error:
        main(["storage-smoke", "--help"])
    output = capsys.readouterr().out

    assert error.value.code == 0
    assert "metadata-only Cloudflare R2 storage smoke test" in output
    assert "never prints storage secrets" in output


def test_storage_smoke_requires_process_env(
    capsys: CaptureFixture[str],
    monkeypatch: MonkeyPatch,
) -> None:
    """Storage smoke should fail before connecting when env is missing."""
    for name in (
        "AEVRYN_STORAGE_PROVIDER",
        "AEVRYN_R2_BUCKET",
        "AEVRYN_R2_ENDPOINT_URL",
        "AEVRYN_R2_ACCESS_KEY_ID",
        "AEVRYN_R2_SECRET_ACCESS_KEY",
    ):
        monkeypatch.delenv(name, raising=False)

    exit_code = main(["storage-smoke"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "AEVRYN_STORAGE_PROVIDER is required" in captured.err


def test_storage_smoke_reads_env_without_printing_credentials(
    capsys: CaptureFixture[str],
    monkeypatch: MonkeyPatch,
) -> None:
    """Storage smoke should print metadata only and never echo R2 credentials."""
    monkeypatch.setenv("AEVRYN_STORAGE_PROVIDER", "r2")
    monkeypatch.setenv("AEVRYN_R2_BUCKET", "aevryn-dev")
    monkeypatch.setenv("AEVRYN_R2_ENDPOINT_URL", "https://account.r2.example")
    monkeypatch.setenv("AEVRYN_R2_ACCESS_KEY_ID", "secret-r2-access-key")
    monkeypatch.setenv("AEVRYN_R2_SECRET_ACCESS_KEY", "secret-r2-secret-key")

    def fake_smoke(
        *,
        bucket: str,
        endpoint_url: str,
        access_key_id: str,
        secret_key: str,
        region_name: str,
    ) -> dict[str, object]:
        assert bucket == "aevryn-dev"
        assert endpoint_url == "https://account.r2.example"
        assert access_key_id == "secret-r2-access-key"
        assert secret_key == "secret-r2-secret-key"
        assert region_name == "auto"
        return {
            "adapter": "r2",
            "bucket": bucket,
            "ok": "storage_r2_smoke_completed",
        }

    monkeypatch.setattr("aevryn.cli._run_r2_storage_smoke", fake_smoke)

    exit_code = main(["storage-smoke"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "adapter=r2" in captured.out
    assert "bucket=aevryn-dev" in captured.out
    assert "ok=storage_r2_smoke_completed" in captured.out
    assert "secret-r2-access-key" not in captured.out
    assert "secret-r2-secret-key" not in captured.out
    assert "secret-r2-access-key" not in captured.err
    assert "secret-r2-secret-key" not in captured.err


def test_worker_drain_help_describes_managed_runner(
    capsys: CaptureFixture[str],
) -> None:
    """Worker drain help should describe the hosted worker runner contract."""
    with pytest.raises(SystemExit) as error:
        main(["worker-drain", "--help"])
    output = capsys.readouterr().out

    assert error.value.code == 0
    assert "Drain queued worker jobs through the hosted API boundary" in output
    assert "--api-url-env" in output
    assert "--worker-key-env" in output
    assert "--max-jobs" in output


def test_worker_drain_requires_process_env(
    capsys: CaptureFixture[str],
    monkeypatch: MonkeyPatch,
) -> None:
    """Worker drain should fail before network access when env is missing."""
    monkeypatch.delenv("AEVRYN_PUBLIC_API_BASE_URL", raising=False)
    monkeypatch.delenv("AEVRYN_WORKER_API_KEY", raising=False)

    exit_code = main(["worker-drain"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "AEVRYN_PUBLIC_API_BASE_URL is required" in captured.err


def test_worker_drain_calls_hosted_api_without_printing_key(
    capsys: CaptureFixture[str],
    monkeypatch: MonkeyPatch,
) -> None:
    """Worker drain should use the worker key without echoing it."""
    monkeypatch.setenv("AEVRYN_PUBLIC_API_BASE_URL", "https://api.aevryn.ai")
    monkeypatch.setenv("AEVRYN_WORKER_API_KEY", "secret-worker-key")
    captured_requests: list[urllib.request.Request] = []

    class FakeResponse:
        status = 200

        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps(
                {
                    "claimed_jobs": 1,
                    "succeeded_jobs": 1,
                    "failed_jobs": 0,
                }
            ).encode("utf-8")

    def fake_urlopen(
        request: urllib.request.Request,
        *,
        timeout: float,
    ) -> FakeResponse:
        captured_requests.append(request)
        assert timeout == 12.5
        return FakeResponse()

    monkeypatch.setattr("aevryn.cli.urllib.request.urlopen", fake_urlopen)

    exit_code = main(
        [
            "worker-drain",
            "--max-jobs",
            "3",
            "--timeout-seconds",
            "12.5",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "claimed_jobs=1" in captured.out
    assert "succeeded_jobs=1" in captured.out
    assert "ok=hosted_worker_drain_completed" in captured.out
    assert "secret-worker-key" not in captured.out
    assert "secret-worker-key" not in captured.err
    request = captured_requests[0]
    assert request.full_url == "https://api.aevryn.ai/v2/workers/process"
    assert request.get_method() == "POST"
    assert request.get_header("X-aevryn-api-key") == "secret-worker-key"
    request_data = request.data
    assert isinstance(request_data, bytes)
    payload = json.loads(request_data.decode("utf-8"))
    assert payload["max_jobs"] == 3
    assert payload["started_at"].endswith("Z")
    assert payload["finished_at"].endswith("Z")


def test_restore_drill_fixture_help_describes_metadata_only_contract(
    capsys: CaptureFixture[str],
) -> None:
    """Restore drill fixture help should describe the hosted API boundary."""
    with pytest.raises(SystemExit) as error:
        main(["restore-drill-fixture", "--help"])
    output = capsys.readouterr().out

    assert error.value.code == 0
    assert "metadata-only restore drill fixture data" in output
    assert "--bearer-token-env" in output
    assert "--drain-worker" in output
    assert "--create-export" in output
    assert "never prints bearer tokens" in output


def test_restore_drill_fixture_requires_process_env(
    capsys: CaptureFixture[str],
    monkeypatch: MonkeyPatch,
) -> None:
    """Restore drill fixture should fail before network access without env."""
    monkeypatch.delenv("AEVRYN_PUBLIC_API_BASE_URL", raising=False)
    monkeypatch.delenv("AEVRYN_RESTORE_DRILL_BEARER_TOKEN", raising=False)

    exit_code = main(["restore-drill-fixture"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "AEVRYN_PUBLIC_API_BASE_URL is required" in captured.err


def test_restore_drill_fixture_prepares_source_data_without_printing_secrets(
    capsys: CaptureFixture[str],
    monkeypatch: MonkeyPatch,
) -> None:
    """Restore drill fixture should use hosted API routes and print metadata only."""
    monkeypatch.setenv("AEVRYN_PUBLIC_API_BASE_URL", "https://api.aevryn.ai")
    monkeypatch.setenv("AEVRYN_RESTORE_DRILL_BEARER_TOKEN", "secret-bearer-token")
    monkeypatch.setenv("AEVRYN_WORKER_API_KEY", "secret-worker-key")
    captured_requests: list[urllib.request.Request] = []

    responses: list[tuple[int, dict[str, object]]] = [
        (200, {"project_id": "created"}),
        (200, {"story_id": "active"}),
        (200, {"story_id": "disposable"}),
        (204, {}),
        (200, {"chapters": 1, "scenes": 2, "evidence_anchors": 6}),
        (200, {"chapter_count": 1, "scene_count": 2}),
        (200, {"run_id": "run", "status": "pending"}),
        (200, {"claimed_jobs": 1, "succeeded_jobs": 1, "failed_jobs": 0}),
        (
            200,
            {
                "latest_engine_run": {"status": "succeeded"},
                "snapshots": {
                    "available": True,
                    "latest_snapshot_id": "snapshot_alpha",
                },
            },
        ),
        (200, {"export_id": "export_alpha"}),
    ]

    class FakeResponse:
        def __init__(self, status: int, payload: dict[str, object]) -> None:
            self.status = status
            self._payload = payload

        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self) -> bytes:
            if self.status == 204:
                return b""
            return json.dumps(self._payload).encode("utf-8")

    def fake_urlopen(
        request: urllib.request.Request,
        *,
        timeout: float,
    ) -> FakeResponse:
        captured_requests.append(request)
        assert timeout == 4.5
        status, payload = responses.pop(0)
        return FakeResponse(status, payload)

    monkeypatch.setattr("aevryn.cli.urllib.request.urlopen", fake_urlopen)

    exit_code = main(
        [
            "restore-drill-fixture",
            "--drain-worker",
            "--create-export",
            "--require-succeeded-run",
            "--timeout-seconds",
            "4.5",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert not responses
    assert "drill_fixture=source" in captured.out
    assert "project_id=restore_drill_project_" in captured.out
    assert "active_story_id=restore_drill_story_" in captured.out
    assert "disposable_story_id=restore_drill_disposable_" in captured.out
    assert "import_id=restore_drill_import_" in captured.out
    assert "run_id=restore_drill_run_" in captured.out
    assert "project_created=True" in captured.out
    assert "disposable_story_deleted=True" in captured.out
    assert "worker_drained=True" in captured.out
    assert "run_status=succeeded" in captured.out
    assert "snapshots_available=True" in captured.out
    assert "export_created=True" in captured.out
    assert "source_bytes_printed=0" in captured.out
    assert "secrets_printed=0" in captured.out
    assert "restore_target_created=False" in captured.out
    assert "public_beta=blocked_until_isolated_restore_drill_passes" in captured.out
    assert "ok=restore_drill_fixture_prepared" in captured.out
    assert "secret-bearer-token" not in captured.out
    assert "secret-worker-key" not in captured.out
    assert "Mira cataloged" not in captured.out
    assert "secret-bearer-token" not in captured.err
    assert "secret-worker-key" not in captured.err

    assert [request.get_method() for request in captured_requests] == [
        "POST",
        "POST",
        "POST",
        "DELETE",
        "POST",
        "POST",
        "POST",
        "POST",
        "GET",
        "POST",
    ]
    assert captured_requests[0].full_url == "https://api.aevryn.ai/v2/projects"
    assert captured_requests[7].full_url == "https://api.aevryn.ai/v2/workers/process"
    assert captured_requests[0].get_header("Authorization") == (
        "Bearer secret-bearer-token"
    )
    assert str(captured_requests[0].get_header("X-aevryn-now")).endswith("Z")
    assert captured_requests[7].get_header("X-aevryn-api-key") == "secret-worker-key"
    assert str(captured_requests[7].get_header("X-aevryn-now")).endswith("Z")
    import_payload = json.loads(cast(bytes, captured_requests[5].data).decode("utf-8"))
    assert import_payload["filename"] == "restore-drill-synthetic.txt"
    assert "content_base64" in import_payload


def test_restore_drill_fixture_can_report_incomplete_without_false_success(
    capsys: CaptureFixture[str],
    monkeypatch: MonkeyPatch,
) -> None:
    """Restore drill fixture should not claim prepared when the run is still pending."""
    monkeypatch.setenv("AEVRYN_PUBLIC_API_BASE_URL", "https://api.aevryn.ai")
    monkeypatch.setenv("AEVRYN_RESTORE_DRILL_BEARER_TOKEN", "secret-bearer-token")

    responses: list[tuple[int, dict[str, object]]] = [
        (200, {"project_id": "created"}),
        (200, {"story_id": "active"}),
        (200, {"story_id": "disposable"}),
        (204, {}),
        (200, {"chapters": 1, "scenes": 2, "evidence_anchors": 6}),
        (200, {"chapter_count": 1, "scene_count": 2}),
        (200, {"run_id": "run", "status": "pending"}),
        (
            200,
            {
                "latest_engine_run": {"status": "pending"},
                "snapshots": {"available": False},
            },
        ),
    ]

    class FakeResponse:
        def __init__(self, status: int, payload: dict[str, object]) -> None:
            self.status = status
            self._payload = payload

        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self) -> bytes:
            if self.status == 204:
                return b""
            return json.dumps(self._payload).encode("utf-8")

    def fake_urlopen(
        request: urllib.request.Request,
        *,
        timeout: float,
    ) -> FakeResponse:
        status, payload = responses.pop(0)
        return FakeResponse(status, payload)

    monkeypatch.setattr("aevryn.cli.urllib.request.urlopen", fake_urlopen)

    exit_code = main(["restore-drill-fixture", "--poll-interval-seconds", "0"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "run_status=pending" in captured.out
    assert "snapshots_available=False" in captured.out
    assert "export_created=False" in captured.out
    assert "ok=restore_drill_fixture_incomplete" in captured.out
    assert "restore_drill_fixture_prepared" not in captured.out
    assert "secret-bearer-token" not in captured.out
    assert "secret-bearer-token" not in captured.err


def test_restore_drill_fixture_can_require_succeeded_run(
    capsys: CaptureFixture[str],
    monkeypatch: MonkeyPatch,
) -> None:
    """Restore drill fixture should fail loudly when success is required."""
    monkeypatch.setenv("AEVRYN_PUBLIC_API_BASE_URL", "https://api.aevryn.ai")
    monkeypatch.setenv("AEVRYN_RESTORE_DRILL_BEARER_TOKEN", "secret-bearer-token")
    responses: list[tuple[int, dict[str, object]]] = [
        (200, {"project_id": "created"}),
        (200, {"story_id": "active"}),
        (200, {"story_id": "disposable"}),
        (204, {}),
        (200, {"chapters": 1, "scenes": 2, "evidence_anchors": 6}),
        (200, {"chapter_count": 1, "scene_count": 2}),
        (200, {"run_id": "run", "status": "pending"}),
        (
            200,
            {
                "latest_engine_run": {"status": "failed"},
                "snapshots": {"available": False},
            },
        ),
    ]

    class FakeResponse:
        def __init__(self, status: int, payload: dict[str, object]) -> None:
            self.status = status
            self._payload = payload

        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self) -> bytes:
            if self.status == 204:
                return b""
            return json.dumps(self._payload).encode("utf-8")

    def fake_urlopen(
        request: urllib.request.Request,
        *,
        timeout: float,
    ) -> FakeResponse:
        status, payload = responses.pop(0)
        return FakeResponse(status, payload)

    monkeypatch.setattr("aevryn.cli.urllib.request.urlopen", fake_urlopen)

    exit_code = main(
        [
            "restore-drill-fixture",
            "--require-succeeded-run",
            "--poll-interval-seconds",
            "0",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "did not reach succeeded state" in captured.err
    assert "secret-bearer-token" not in captured.out
    assert "secret-bearer-token" not in captured.err


def test_restore_drill_fixture_reports_safe_http_error_detail(
    capsys: CaptureFixture[str],
    monkeypatch: MonkeyPatch,
) -> None:
    """Restore drill fixture failures should identify the route without leaking secrets."""
    monkeypatch.setenv("AEVRYN_PUBLIC_API_BASE_URL", "https://api.aevryn.ai")
    monkeypatch.setenv("AEVRYN_RESTORE_DRILL_BEARER_TOKEN", "secret-bearer-token")

    def fake_urlopen(
        request: urllib.request.Request,
        *,
        timeout: float,
    ) -> object:
        raise urllib.error.HTTPError(
            url=request.full_url,
            code=400,
            msg="Bad Request",
            hdrs=cast(Any, {}),
            fp=BytesIO(
                json.dumps(
                    {
                        "detail": {
                            "error": "project_create_failed",
                            "detail": "bad request with secret-bearer-token",
                        }
                    }
                ).encode("utf-8")
            ),
        )

    monkeypatch.setattr("aevryn.cli.urllib.request.urlopen", fake_urlopen)

    exit_code = main(["restore-drill-fixture"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "restore-drill-fixture POST /v2/projects failed with HTTP 400" in captured.err
    assert "project_create_failed" in captured.err
    assert "secret-bearer-token" not in captured.out
    assert "secret-bearer-token" not in captured.err


def test_restore_drill_verify_help_describes_metadata_only_contract(
    capsys: CaptureFixture[str],
) -> None:
    """Restore drill verifier help should describe the isolated API boundary."""
    with pytest.raises(SystemExit) as error:
        main(["restore-drill-verify", "--help"])
    output = capsys.readouterr().out

    assert error.value.code == 0
    assert "Verify restored API ownership and deletion boundaries" in output
    assert "--other-bearer-token-env" in output
    assert "without printing tokens" in output


def test_restore_drill_verify_rejects_public_api_domain_by_default(
    capsys: CaptureFixture[str],
    monkeypatch: MonkeyPatch,
) -> None:
    """Restore drill verifier should fail closed when pointed at production."""
    monkeypatch.setenv("AEVRYN_PUBLIC_API_BASE_URL", "https://api.aevryn.ai")
    monkeypatch.setenv("AEVRYN_RESTORE_DRILL_BEARER_TOKEN", "owner-token")
    monkeypatch.setenv("AEVRYN_RESTORE_DRILL_OTHER_BEARER_TOKEN", "other-token")

    exit_code = main(
        [
            "restore-drill-verify",
            "--project-id",
            "project_restore",
            "--active-story-id",
            "story_active",
            "--disposable-story-id",
            "story_deleted",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "requires an isolated API URL" in captured.err
    assert "owner-token" not in captured.out
    assert "owner-token" not in captured.err


def test_restore_drill_verify_can_prompt_for_session_tokens(
    capsys: CaptureFixture[str],
    monkeypatch: MonkeyPatch,
) -> None:
    """Restore drill verifier should support hidden interactive session tokens."""
    monkeypatch.setenv("AEVRYN_PUBLIC_API_BASE_URL", "https://api.aevryn.ai")
    monkeypatch.delenv("AEVRYN_RESTORE_DRILL_BEARER_TOKEN", raising=False)
    monkeypatch.delenv("AEVRYN_RESTORE_DRILL_OTHER_BEARER_TOKEN", raising=False)
    prompted_values = iter(("owner-token", "other-token"))

    def fake_prompt(prompt: str) -> str:
        assert "session token" in prompt
        return next(prompted_values)

    monkeypatch.setattr("aevryn.cli.getpass.getpass", fake_prompt)

    exit_code = main(
        [
            "restore-drill-verify",
            "--prompt-session-tokens",
            "--project-id",
            "project_restore",
            "--active-story-id",
            "story_active",
            "--disposable-story-id",
            "story_deleted",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "requires an isolated API URL" in captured.err
    assert "owner-token" not in captured.out
    assert "other-token" not in captured.out
    assert "owner-token" not in captured.err
    assert "other-token" not in captured.err


def test_restore_drill_verify_can_read_session_tokens_from_clipboard(
    capsys: CaptureFixture[str],
    monkeypatch: MonkeyPatch,
) -> None:
    """Restore drill verifier should support clipboard tokens for Windows drills."""
    monkeypatch.setenv("AEVRYN_PUBLIC_API_BASE_URL", "https://api.aevryn.ai")
    monkeypatch.delenv("AEVRYN_RESTORE_DRILL_BEARER_TOKEN", raising=False)
    monkeypatch.delenv("AEVRYN_RESTORE_DRILL_OTHER_BEARER_TOKEN", raising=False)
    clipboard_values = iter(("owner-token", "other-token"))

    def fake_input(prompt: str) -> str:
        assert "Do not paste it here" in prompt
        return ""

    monkeypatch.setattr("builtins.input", fake_input)
    monkeypatch.setattr(
        "aevryn.cli._read_clipboard_text",
        lambda: next(clipboard_values),
    )

    exit_code = main(
        [
            "restore-drill-verify",
            "--clipboard-session-tokens",
            "--project-id",
            "project_restore",
            "--active-story-id",
            "story_active",
            "--disposable-story-id",
            "story_deleted",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "requires an isolated API URL" in captured.err
    assert "owner-token" not in captured.out
    assert "other-token" not in captured.out
    assert "owner-token" not in captured.err
    assert "other-token" not in captured.err


def test_restore_drill_verify_rejects_combined_interactive_token_modes(
    capsys: CaptureFixture[str],
    monkeypatch: MonkeyPatch,
) -> None:
    """Restore drill verifier should fail closed when token input modes conflict."""
    monkeypatch.setenv("AEVRYN_PUBLIC_API_BASE_URL", "https://api.aevryn.ai")

    exit_code = main(
        [
            "restore-drill-verify",
            "--prompt-session-tokens",
            "--clipboard-session-tokens",
            "--project-id",
            "project_restore",
            "--active-story-id",
            "story_active",
            "--disposable-story-id",
            "story_deleted",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "cannot both be used" in captured.err


def test_restore_drill_verify_checks_api_boundaries_without_printing_private_data(
    capsys: CaptureFixture[str],
    monkeypatch: MonkeyPatch,
) -> None:
    """Restore drill verifier should prove ownership boundaries with metadata only."""
    monkeypatch.setenv("AEVRYN_PUBLIC_API_BASE_URL", "https://restore-api.aevryn.test")
    monkeypatch.setenv("AEVRYN_RESTORE_DRILL_BEARER_TOKEN", "owner-token")
    monkeypatch.setenv("AEVRYN_RESTORE_DRILL_OTHER_BEARER_TOKEN", "other-token")
    monkeypatch.setenv("AEVRYN_RESTORE_DRILL_CLOUD_RUN_IDENTITY_TOKEN", "cloud-run-token")
    captured_requests: list[urllib.request.Request] = []

    responses: list[tuple[int, dict[str, object] | bytes]] = [
        (200, {"project_id": "project_restore"}),
        (
            200,
            {
                "stories": (
                    {"story_id": "story_active"},
                    {"story_id": "story_other"},
                )
            },
        ),
        (
            200,
            {
                "imports": (
                    {
                        "import_id": "import_restore",
                        "storage_ref": "storage://private/source",
                    },
                )
            },
        ),
        (
            200,
            {
                "status": "succeeded",
                "snapshots": {"available": True},
            },
        ),
        (
            200,
            {
                "exports": (
                    {
                        "export_id": "export_restore",
                        "checksum": "abc123",
                    },
                )
            },
        ),
        (200, b'{"private":"export body"}'),
        (404, {}),
        (404, {}),
        (404, {}),
        (404, {}),
        (404, {}),
    ]

    class FakeResponse:
        def __init__(self, status: int, payload: dict[str, object] | bytes) -> None:
            self.status = status
            self._payload = payload

        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self) -> bytes:
            if isinstance(self._payload, bytes):
                return self._payload
            return json.dumps(self._payload).encode("utf-8")

    def fake_urlopen(
        request: urllib.request.Request,
        *,
        timeout: float,
    ) -> FakeResponse:
        captured_requests.append(request)
        assert timeout == 4.5
        status, payload = responses.pop(0)
        if status >= 400:
            raise urllib.error.HTTPError(
                url=request.full_url,
                code=status,
                msg="Denied",
                hdrs=cast(Any, {}),
                fp=BytesIO(b'{"detail":{"error":"not_found"}}'),
            )
        return FakeResponse(status, payload)

    monkeypatch.setattr("aevryn.cli.urllib.request.urlopen", fake_urlopen)

    exit_code = main(
        [
            "restore-drill-verify",
            "--project-id",
            "project_restore",
            "--active-story-id",
            "story_active",
            "--disposable-story-id",
            "story_deleted",
            "--import-id",
            "import_restore",
            "--export-id",
            "export_restore",
            "--timeout-seconds",
            "4.5",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert not responses
    assert "drill_verification=isolated_api" in captured.out
    assert "owner_project_read=passed" in captured.out
    assert "deleted_story_absent_from_product_surfaces=passed" in captured.out
    assert "source_storage_owner_scoped=passed" in captured.out
    assert "export_storage_owner_scoped=passed" in captured.out
    assert "cross_user_project_read=denied" in captured.out
    assert "cross_user_export_download=denied" in captured.out
    assert "source_bytes_printed=0" in captured.out
    assert "export_bytes_printed=0" in captured.out
    assert "storage_refs_printed=0" in captured.out
    assert "secrets_printed=0" in captured.out
    assert "private_cloud_run_auth=present" in captured.out
    assert "ok=restore_drill_api_boundaries_verified" in captured.out
    assert "owner-token" not in captured.out
    assert "other-token" not in captured.out
    assert "cloud-run-token" not in captured.out
    assert "storage://private/source" not in captured.out
    assert "export body" not in captured.out
    assert "owner-token" not in captured.err
    assert "other-token" not in captured.err
    assert "cloud-run-token" not in captured.err

    assert [request.get_method() for request in captured_requests] == [
        "GET",
        "GET",
        "GET",
        "GET",
        "GET",
        "GET",
        "GET",
        "GET",
        "GET",
        "GET",
        "GET",
    ]
    assert captured_requests[0].full_url == (
        "https://restore-api.aevryn.test/v2/projects/project_restore"
    )
    assert captured_requests[5].full_url == (
        "https://restore-api.aevryn.test/v2/projects/project_restore"
        "/exports/export_restore/download"
    )
    assert captured_requests[0].get_header("Authorization") == "Bearer owner-token"
    request_now = captured_requests[0].get_header("X-aevryn-now")
    assert request_now
    assert all(
        request.get_header("X-aevryn-now") == request_now
        for request in captured_requests
    )
    assert (
        captured_requests[0].get_header("X-serverless-authorization")
        == "Bearer cloud-run-token"
    )
    assert captured_requests[6].get_header("Authorization") == "Bearer other-token"
    assert (
        captured_requests[6].get_header("X-serverless-authorization")
        == "Bearer cloud-run-token"
    )


def test_restore_api_config_check_help_describes_isolated_contract(
    capsys: CaptureFixture[str],
) -> None:
    """Restore API config check help should describe the isolated target contract."""
    with pytest.raises(SystemExit) as error:
        main(["restore-api-config-check", "--help"])
    output = capsys.readouterr().out

    assert error.value.code == 0
    assert "Check isolated restore API configuration without printing secrets" in output
    assert "not pointed at the public production API domain" in output


def test_restore_api_config_check_requires_explicit_restore_target(
    capsys: CaptureFixture[str],
    monkeypatch: MonkeyPatch,
) -> None:
    """Restore API config check should require an explicit restore-drill target flag."""
    monkeypatch.setenv("AEVRYN_DEPLOYMENT_ENV", "production")
    monkeypatch.delenv("AEVRYN_RESTORE_DRILL_TARGET", raising=False)

    exit_code = main(["restore-api-config-check"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "AEVRYN_RESTORE_DRILL_TARGET=true is required" in captured.err


def test_restore_api_config_check_rejects_public_api_domain(
    capsys: CaptureFixture[str],
    monkeypatch: MonkeyPatch,
) -> None:
    """Restore API config check should fail closed on the production API domain."""
    monkeypatch.setenv("AEVRYN_DEPLOYMENT_ENV", "production")
    monkeypatch.setenv("AEVRYN_RESTORE_DRILL_TARGET", "true")
    monkeypatch.setenv("AEVRYN_ENVIRONMENT_NAME", "restore-drill")
    monkeypatch.setenv("AEVRYN_PUBLIC_API_BASE_URL", "https://api.aevryn.ai")

    exit_code = main(["restore-api-config-check"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "requires an isolated API URL" in captured.err


def test_restore_api_config_check_reports_metadata_without_private_values(
    capsys: CaptureFixture[str],
    monkeypatch: MonkeyPatch,
) -> None:
    """Restore API config check should report metadata without private values."""
    private_values = (
        "postgresql://runtime:private-value@restore.invalid/postgres",
        "restore-bucket-private-value",
    )
    env_values = {
        "AEVRYN_DEPLOYMENT_ENV": "production",
        "AEVRYN_RESTORE_DRILL_TARGET": "true",
        "AEVRYN_ENVIRONMENT_NAME": "restore-drill",
        "AEVRYN_PUBLIC_API_BASE_URL": "https://restore-api.aevryn.test",
        "AEVRYN_PROJECT_DATABASE_ADAPTER": "postgresql",
        "AEVRYN_PROJECT_DATABASE_URL": private_values[0],
        "AEVRYN_PROJECT_DATABASE_BOOTSTRAP": "false",
        "AEVRYN_STORAGE_PROVIDER": "r2",
        "AEVRYN_R2_BUCKET": private_values[1],
        "AEVRYN_SECRET_MANAGER": "deployment",
        "AEVRYN_LOG_DESTINATION": "hosted",
        "AEVRYN_MONITORING_DESTINATION": "hosted",
        "AEVRYN_SECURITY_ALERTS_ENABLED": "true",
        "AEVRYN_METADATA_ONLY_LOGGING": "true",
    }
    for key, value in env_values.items():
        monkeypatch.setenv(key, value)

    exit_code = main(["restore-api-config-check"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "restore_target=isolated_api" in captured.out
    assert "environment_name=restore-drill" in captured.out
    assert "public_api_is_production_domain=false" in captured.out
    assert "project_database_bootstrap=false" in captured.out
    assert "production_traffic_attached=false" in captured.out
    assert "secrets_printed=0" in captured.out
    assert "ok=restore_api_config_contract_checked" in captured.out
    for private_value in private_values:
        assert private_value not in captured.out
        assert private_value not in captured.err


def test_production_config_check_help_describes_metadata_only_contract(
    capsys: CaptureFixture[str],
) -> None:
    """Production config check help should describe the metadata-only contract."""
    with pytest.raises(SystemExit) as error:
        main(["production-config-check", "--help"])
    output = capsys.readouterr().out

    assert error.value.code == 0
    assert "Check production startup configuration without printing secrets" in output
    assert "public-beta approval boundary" in output


def test_production_config_check_requires_production_env(
    capsys: CaptureFixture[str],
    monkeypatch: MonkeyPatch,
) -> None:
    """Production config check should fail before local app startup."""
    monkeypatch.delenv("AEVRYN_DEPLOYMENT_ENV", raising=False)

    exit_code = main(["production-config-check"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "AEVRYN_DEPLOYMENT_ENV=production is required" in captured.err


def test_production_config_check_reports_ready_contract_without_secrets(
    capsys: CaptureFixture[str],
    monkeypatch: MonkeyPatch,
) -> None:
    """Production config check should print metadata and no secret values."""
    secret_values = (
        "secret-db-password",
        "secret-r2-access-key",
        "secret-r2-secret-key",
        "secret-worker-key",
        "secret-session-value",
        "secret-api-key",
        "secret-supabase-anon-key",
        "secret-supabase-service-role-key",
    )
    env_values = {
        "AEVRYN_DEPLOYMENT_ENV": "production",
        "AEVRYN_PROJECT_DATABASE_ADAPTER": "postgresql",
        "AEVRYN_PROJECT_DATABASE_BOOTSTRAP": "false",
        "AEVRYN_PROJECT_DATABASE_URL": (
            "postgresql://aevryn_app:secret-db-password@localhost:5432/aevryn_dev"
        ),
        "AEVRYN_API_ALLOWED_ORIGINS": "https://app.aevryn.ai",
        "AEVRYN_PUBLIC_FRONTEND_BASE_URL": "https://app.aevryn.ai",
        "AEVRYN_PUBLIC_API_BASE_URL": "https://api.aevryn.ai",
        "AEVRYN_HTTPS_ONLY": "true",
        "AEVRYN_HSTS_ENABLED": "true",
        "AEVRYN_API_KEYS": "secret-api-key",
        "AEVRYN_STORAGE_PROVIDER": "r2",
        "AEVRYN_R2_BUCKET": "aevryn-prod",
        "AEVRYN_R2_ACCOUNT_ID": "account-id",
        "AEVRYN_R2_ENDPOINT_URL": "https://account-id.r2.cloudflarestorage.com",
        "AEVRYN_R2_ACCESS_KEY_ID": "secret-r2-access-key",
        "AEVRYN_R2_SECRET_ACCESS_KEY": "secret-r2-secret-key",
        "AEVRYN_SECRET_MANAGER": "deployment",
        "AEVRYN_ENVIRONMENT_NAME": "production",
        "AEVRYN_WORKER_RUNTIME": "managed",
        "AEVRYN_WORKER_QUEUE_PROVIDER": "managed",
        "AEVRYN_WORKER_API_KEY": "secret-worker-key",
        "AEVRYN_WORKER_TIMEOUT_SECONDS": "120",
        "AEVRYN_WORKER_MAX_RETRIES": "3",
        "AEVRYN_WORKER_CONCURRENCY": "1",
        "AEVRYN_LOG_DESTINATION": "hosted",
        "AEVRYN_MONITORING_DESTINATION": "hosted",
        "AEVRYN_LOG_RETENTION_DAYS": "30",
        "AEVRYN_MONITORING_RETENTION_DAYS": "30",
        "AEVRYN_SECURITY_ALERTS_ENABLED": "true",
        "AEVRYN_METADATA_ONLY_LOGGING": "true",
        "AEVRYN_IDENTITY_PROVIDER": "managed",
        "AEVRYN_IDENTITY_PROVIDER_NAME": "supabase",
        "AEVRYN_SUPABASE_URL": "https://aevryn-dev.supabase.co",
        "AEVRYN_SUPABASE_JWKS_URL": (
            "https://aevryn-dev.supabase.co/auth/v1/.well-known/jwks.json"
        ),
        "AEVRYN_SUPABASE_ANON_KEY": "secret-supabase-anon-key",
        "AEVRYN_SUPABASE_SERVICE_ROLE_KEY": "secret-supabase-service-role-key",
        "AEVRYN_SESSION_AUTHORITY": "bearer",
        "AEVRYN_SESSION_SECRET": "secret-session-value",
        "AEVRYN_PASSWORD_RESET_ENABLED": "true",
        "AEVRYN_ACCOUNT_DELETION_HANDOFF_CONFIGURED": "true",
    }
    for key, value in env_values.items():
        monkeypatch.setenv(key, value)

    def fake_create_app_from_env(environ: dict[str, str]) -> object:
        assert environ["AEVRYN_IDENTITY_PROVIDER_NAME"] == "supabase"
        assert environ["AEVRYN_SUPABASE_ANON_KEY"] == "secret-supabase-anon-key"
        return object()

    monkeypatch.setattr("aevryn.cli.create_app_from_env", fake_create_app_from_env)

    exit_code = main(["production-config-check"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "deployment_env=production" in captured.out
    assert "startup_contract=ready" in captured.out
    assert "public_beta=not_approved_until_gate_signoff" in captured.out
    assert "secrets_printed=0" in captured.out
    assert "ok=production_config_contract_checked" in captured.out
    for secret_value in secret_values:
        assert secret_value not in captured.out
        assert secret_value not in captured.err


def test_production_config_check_audits_failures_when_ledger_is_available(
    monkeypatch: MonkeyPatch,
) -> None:
    """Production config failures should append stable metadata-only audit records."""
    appended_records: list[dict[str, object]] = []

    class FakePostgresqlAuditLedger:
        """Capture audit writes without connecting to PostgreSQL."""

        def __init__(self, database_url: str) -> None:
            self.database_url = database_url

        def append(self, **kwargs: object) -> object:
            appended_records.append(kwargs)
            return object()

    monkeypatch.setattr("aevryn.cli.PostgresqlAuditLedger", FakePostgresqlAuditLedger)

    with pytest.raises(ValueError, match="AEVRYN_API_ALLOWED_ORIGINS") as error:
        _run_production_config_check(
            {
                "AEVRYN_DEPLOYMENT_ENV": "production",
                "AEVRYN_PROJECT_DATABASE_ADAPTER": "postgresql",
                "AEVRYN_PROJECT_DATABASE_URL": (
                    "postgresql://aevryn_app:secret-db-password@localhost/aevryn"
                ),
            }
        )
    assert "AEVRYN_API_ALLOWED_ORIGINS" in str(error.value)
    assert "secret-db-password" not in str(error.value)
    assert "audit was not recorded" not in str(error.value)

    assert appended_records == [
        {
            "event_type": "security_configuration_failed",
            "occurred_at": appended_records[0]["occurred_at"],
            "summary": "Production config check failed.",
            "metadata": {
                "failure_code": "missing_or_invalid_aevryn_api_allowed_origins",
            },
        }
    ]
    serialized_record = json.dumps(appended_records[0], sort_keys=True)
    assert "secret-db-password" not in serialized_record
    assert "postgresql://" not in serialized_record


def test_production_config_check_preserves_failure_when_audit_unavailable(
    monkeypatch: MonkeyPatch,
) -> None:
    """Audit unavailability should not hide the original config failure."""

    class UnavailablePostgresqlAuditLedger:
        """Fail construction to simulate an unreachable audit database."""

        def __init__(self, _database_url: str) -> None:
            raise RuntimeError("audit storage unavailable")

    monkeypatch.setattr(
        "aevryn.cli.PostgresqlAuditLedger",
        UnavailablePostgresqlAuditLedger,
    )

    with pytest.raises(ValueError, match="audit was not recorded") as error:
        _run_production_config_check(
            {
                "AEVRYN_DEPLOYMENT_ENV": "production",
                "AEVRYN_PROJECT_DATABASE_ADAPTER": "postgresql",
                "AEVRYN_PROJECT_DATABASE_URL": (
                    "postgresql://aevryn_app:secret-db-password@localhost/aevryn"
                ),
            }
        )
    assert "AEVRYN_API_ALLOWED_ORIGINS" in str(error.value)
    assert "secret-db-password" not in str(error.value)


def test_observability_config_check_help_describes_bounded_log_review(
    capsys: CaptureFixture[str],
) -> None:
    """Observability check help should distinguish config from log review."""
    with pytest.raises(SystemExit) as error:
        main(["observability-config-check", "--help"])
    output = capsys.readouterr().out

    assert error.value.code == 0
    assert "hosted observability configuration" in output
    assert "does not replace the required bounded hosted log review" in output


def test_observability_config_check_reports_metadata_only_contract(
    capsys: CaptureFixture[str],
    monkeypatch: MonkeyPatch,
) -> None:
    """Observability config check should print metadata and no secret values."""
    env_values = {
        "AEVRYN_DEPLOYMENT_ENV": "production",
        "AEVRYN_LOG_DESTINATION": "hosted",
        "AEVRYN_MONITORING_DESTINATION": "hosted",
        "AEVRYN_LOG_RETENTION_DAYS": "30",
        "AEVRYN_MONITORING_RETENTION_DAYS": "14",
        "AEVRYN_SECURITY_ALERTS_ENABLED": "true",
        "AEVRYN_METADATA_ONLY_LOGGING": "true",
        "AEVRYN_API_KEYS": "secret-api-key",
        "AEVRYN_PROJECT_DATABASE_URL": (
            "postgresql://aevryn_app:secret-db-password@localhost/aevryn"
        ),
    }
    for key, value in env_values.items():
        monkeypatch.setenv(key, value)

    exit_code = main(["observability-config-check"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "deployment_env=production" in captured.out
    assert "log_destination=hosted" in captured.out
    assert "monitoring_destination=hosted" in captured.out
    assert "log_retention_days=30" in captured.out
    assert "monitoring_retention_days=14" in captured.out
    assert "security_alerts_enabled=true" in captured.out
    assert "metadata_only_logging=true" in captured.out
    assert "bounded_hosted_log_review=required" in captured.out
    assert "public_beta=blocked_until_bounded_hosted_log_review" in captured.out
    assert "secrets_printed=0" in captured.out
    assert "ok=observability_config_contract_checked" in captured.out
    assert "secret-api-key" not in captured.out
    assert "secret-db-password" not in captured.out
    assert "postgresql://" not in captured.out
    assert "secret-api-key" not in captured.err
    assert "secret-db-password" not in captured.err
    assert "postgresql://" not in captured.err


def test_observability_config_check_rejects_local_log_destination() -> None:
    """Public-beta observability should fail closed for local-only logs."""
    with pytest.raises(ValueError, match="AEVRYN_LOG_DESTINATION=hosted"):
        _run_observability_config_check(
            {
                "AEVRYN_DEPLOYMENT_ENV": "production",
                "AEVRYN_LOG_DESTINATION": "local",
                "AEVRYN_MONITORING_DESTINATION": "hosted",
                "AEVRYN_LOG_RETENTION_DAYS": "30",
                "AEVRYN_MONITORING_RETENTION_DAYS": "30",
                "AEVRYN_SECURITY_ALERTS_ENABLED": "true",
                "AEVRYN_METADATA_ONLY_LOGGING": "true",
            }
        )


def test_observability_config_check_rejects_unbounded_retention() -> None:
    """Operational observability retention should stay within the policy maximum."""
    with pytest.raises(ValueError, match="AEVRYN_LOG_RETENTION_DAYS"):
        _run_observability_config_check(
            {
                "AEVRYN_DEPLOYMENT_ENV": "production",
                "AEVRYN_LOG_DESTINATION": "hosted",
                "AEVRYN_MONITORING_DESTINATION": "hosted",
                "AEVRYN_LOG_RETENTION_DAYS": "90",
                "AEVRYN_MONITORING_RETENTION_DAYS": "30",
                "AEVRYN_SECURITY_ALERTS_ENABLED": "true",
                "AEVRYN_METADATA_ONLY_LOGGING": "true",
            }
        )


def test_observability_config_check_requires_metadata_only_logging() -> None:
    """Observability readiness should require explicit metadata-only logging."""
    with pytest.raises(ValueError, match="AEVRYN_METADATA_ONLY_LOGGING=true"):
        _run_observability_config_check(
            {
                "AEVRYN_DEPLOYMENT_ENV": "production",
                "AEVRYN_LOG_DESTINATION": "hosted",
                "AEVRYN_MONITORING_DESTINATION": "hosted",
                "AEVRYN_LOG_RETENTION_DAYS": "30",
                "AEVRYN_MONITORING_RETENTION_DAYS": "30",
                "AEVRYN_SECURITY_ALERTS_ENABLED": "true",
                "AEVRYN_METADATA_ONLY_LOGGING": "false",
            }
        )


def test_audit_ledger_verify_help_describes_metadata_only_contract(
    capsys: CaptureFixture[str],
) -> None:
    """Audit verify help should describe the metadata-only release gate."""
    with pytest.raises(SystemExit) as error:
        main(["audit-ledger-verify", "--help"])
    output = capsys.readouterr().out

    assert error.value.code == 0
    assert "Verify the PostgreSQL audit ledger hash chain" in output
    assert "without printing secrets" in output


def test_audit_ledger_verify_requires_database_url_env(
    capsys: CaptureFixture[str],
    monkeypatch: MonkeyPatch,
) -> None:
    """Audit verify should fail closed when the database URL is absent."""
    monkeypatch.delenv("AEVRYN_PROJECT_DATABASE_URL", raising=False)

    exit_code = main(["audit-ledger-verify"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "AEVRYN_PROJECT_DATABASE_URL is required" in captured.err


def test_audit_ledger_verify_reports_metadata_without_secrets(
    capsys: CaptureFixture[str],
    monkeypatch: MonkeyPatch,
) -> None:
    """Audit verify should report counts and never print the database URL."""
    secret_database_url = "postgresql://aevryn_app:secret-db-password@localhost/aevryn"

    class FakePostgresqlAuditLedger:
        """Fake ledger for deterministic CLI verification tests."""

        def __init__(self, database_url: str, *, bootstrap_schema: bool = True) -> None:
            assert database_url == secret_database_url
            assert bootstrap_schema is False

        def verify(self) -> None:
            return None

        def records(self) -> tuple[object, ...]:
            return (object(), object(), object())

    monkeypatch.setenv("AEVRYN_PROJECT_DATABASE_URL", secret_database_url)
    monkeypatch.setattr("aevryn.cli.PostgresqlAuditLedger", FakePostgresqlAuditLedger)

    exit_code = main(["audit-ledger-verify"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "adapter=postgresql" in captured.out
    assert "ledger=audit" in captured.out
    assert "records_verified=3" in captured.out
    assert "secrets_printed=0" in captured.out
    assert "ok=audit_ledger_postgresql_integrity_verified" in captured.out
    assert "secret-db-password" not in captured.out
    assert "postgresql://" not in captured.out
    assert "secret-db-password" not in captured.err
    assert "postgresql://" not in captured.err


def test_audit_ledger_verify_propagates_integrity_failure_without_database_url(
    monkeypatch: MonkeyPatch,
) -> None:
    """Audit verify should fail visibly without printing database credentials."""
    secret_database_url = "postgresql://aevryn_app:secret-db-password@localhost/aevryn"

    class TamperedPostgresqlAuditLedger:
        """Fake ledger that fails hash-chain verification."""

        def __init__(self, database_url: str, *, bootstrap_schema: bool = True) -> None:
            assert database_url == secret_database_url
            assert bootstrap_schema is False

        def verify(self) -> None:
            raise ValueError("Audit ledger record hash is invalid.")

    monkeypatch.setattr("aevryn.cli.PostgresqlAuditLedger", TamperedPostgresqlAuditLedger)

    with pytest.raises(ValueError, match="record hash"):
        _run_audit_ledger_verify(database_url=secret_database_url)


def test_audit_access_report_help_describes_metadata_only_contract(
    capsys: CaptureFixture[str],
) -> None:
    """Audit access help should describe the secret-safe report contract."""
    with pytest.raises(SystemExit) as error:
        main(["audit-access-report", "--help"])
    output = capsys.readouterr().out

    assert error.value.code == 0
    assert "Report PostgreSQL audit table access metadata" in output
    assert "without printing secrets" in output


def test_audit_access_report_requires_database_url_env(
    capsys: CaptureFixture[str],
    monkeypatch: MonkeyPatch,
) -> None:
    """Audit access reporting should fail closed when config is absent."""
    monkeypatch.delenv("AEVRYN_PROJECT_DATABASE_URL", raising=False)

    exit_code = main(["audit-access-report"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "AEVRYN_PROJECT_DATABASE_URL is required" in captured.err


def test_audit_access_report_prints_privileges_without_secrets(
    capsys: CaptureFixture[str],
    monkeypatch: MonkeyPatch,
) -> None:
    """Audit access reporting should print only metadata privilege booleans."""
    secret_database_url = "postgresql://aevryn_app:secret-db-password@localhost/aevryn"

    def fake_access_report(database_url: str) -> dict[str, object]:
        assert database_url == secret_database_url
        return {
            "table_exists": True,
            "can_select": True,
            "can_insert": True,
            "can_update": False,
            "can_delete": False,
            "can_truncate": False,
            "is_table_owner": False,
        }

    monkeypatch.setenv("AEVRYN_PROJECT_DATABASE_URL", secret_database_url)
    monkeypatch.setattr("aevryn.cli.postgresql_audit_access_report", fake_access_report)

    exit_code = main(["audit-access-report"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "adapter=postgresql" in captured.out
    assert "ledger=audit" in captured.out
    assert "table_exists=true" in captured.out
    assert "can_select=true" in captured.out
    assert "can_insert=true" in captured.out
    assert "can_update=false" in captured.out
    assert "can_delete=false" in captured.out
    assert "can_truncate=false" in captured.out
    assert "is_table_owner=false" in captured.out
    assert "secrets_printed=0" in captured.out
    assert "ok=audit_access_metadata_reported" in captured.out
    assert "secret-db-password" not in captured.out
    assert "postgresql://" not in captured.out
    assert "localhost" not in captured.out
    assert "aevryn_app" not in captured.out


def test_audit_access_report_helper_returns_stable_boolean_text(
    monkeypatch: MonkeyPatch,
) -> None:
    """Audit access helper should normalize booleans for release records."""

    def fake_access_report(database_url: str) -> dict[str, object]:
        assert database_url == "postgresql://example.invalid/aevryn"
        return {
            "table_exists": True,
            "can_select": True,
            "can_insert": False,
            "can_update": False,
            "can_delete": False,
            "can_truncate": False,
            "is_table_owner": False,
        }

    monkeypatch.setattr("aevryn.cli.postgresql_audit_access_report", fake_access_report)

    assert _run_audit_access_report(
        database_url="postgresql://example.invalid/aevryn"
    ) == {
        "adapter": "postgresql",
        "ledger": "audit",
        "table_exists": "true",
        "can_select": "true",
        "can_insert": "false",
        "can_update": "false",
        "can_delete": "false",
        "can_truncate": "false",
        "is_table_owner": "false",
        "secrets_printed": 0,
        "ok": "audit_access_metadata_reported",
    }


def test_audit_access_verify_help_describes_append_only_contract(
    capsys: CaptureFixture[str],
) -> None:
    """Audit access verify help should describe append-only privilege checks."""
    with pytest.raises(SystemExit) as error:
        main(["audit-access-verify", "--help"])
    output = capsys.readouterr().out

    assert error.value.code == 0
    assert "append-only" in output
    assert "must not be able to update, delete, or truncate" in output


def test_audit_access_verify_reports_success_without_secrets(
    capsys: CaptureFixture[str],
    monkeypatch: MonkeyPatch,
) -> None:
    """Audit access verify should pass with read/insert and no update/delete."""
    secret_database_url = "postgresql://aevryn_app:secret-db-password@localhost/aevryn"

    def fake_access_report(database_url: str) -> dict[str, object]:
        assert database_url == secret_database_url
        return {
            "table_exists": True,
            "can_select": True,
            "can_insert": True,
            "can_update": False,
            "can_delete": False,
            "can_truncate": False,
            "is_table_owner": False,
        }

    monkeypatch.setenv("AEVRYN_PROJECT_DATABASE_URL", secret_database_url)
    monkeypatch.setattr("aevryn.cli.postgresql_audit_access_report", fake_access_report)

    exit_code = main(["audit-access-verify"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "ok=audit_access_append_only_verified" in captured.out
    assert "can_update=false" in captured.out
    assert "can_delete=false" in captured.out
    assert "can_truncate=false" in captured.out
    assert "is_table_owner=false" in captured.out
    assert "secret-db-password" not in captured.out
    assert "postgresql://" not in captured.out
    assert "localhost" not in captured.out
    assert "aevryn_app" not in captured.out


@pytest.mark.parametrize(
    ("report", "expected_error"),
    (
        (
            {
                "table_exists": False,
                "can_select": False,
                "can_insert": False,
                "can_update": False,
                "can_delete": False,
                "can_truncate": False,
                "is_table_owner": False,
            },
            "audit table is missing",
        ),
        (
            {
                "table_exists": True,
                "can_select": False,
                "can_insert": True,
                "can_update": False,
                "can_delete": False,
                "can_truncate": False,
                "is_table_owner": False,
            },
            "lacks SELECT privilege",
        ),
        (
            {
                "table_exists": True,
                "can_select": True,
                "can_insert": False,
                "can_update": False,
                "can_delete": False,
                "can_truncate": False,
                "is_table_owner": False,
            },
            "lacks INSERT privilege",
        ),
        (
            {
                "table_exists": True,
                "can_select": True,
                "can_insert": True,
                "can_update": True,
                "can_delete": False,
                "can_truncate": False,
                "is_table_owner": False,
            },
            "UPDATE privilege is present",
        ),
        (
            {
                "table_exists": True,
                "can_select": True,
                "can_insert": True,
                "can_update": False,
                "can_delete": True,
                "can_truncate": False,
                "is_table_owner": False,
            },
            "DELETE privilege is present",
        ),
        (
            {
                "table_exists": True,
                "can_select": True,
                "can_insert": True,
                "can_update": False,
                "can_delete": False,
                "can_truncate": True,
                "is_table_owner": False,
            },
            "TRUNCATE privilege is present",
        ),
        (
            {
                "table_exists": True,
                "can_select": True,
                "can_insert": True,
                "can_update": False,
                "can_delete": False,
                "can_truncate": False,
                "is_table_owner": True,
            },
            "runtime role owns the audit table",
        ),
    ),
)
def test_audit_access_verify_fails_closed_for_unsafe_privileges(
    monkeypatch: MonkeyPatch,
    report: dict[str, object],
    expected_error: str,
) -> None:
    """Audit access verify should reject missing or unsafe table privileges."""

    def fake_access_report(database_url: str) -> dict[str, object]:
        assert database_url == "postgresql://example.invalid/aevryn"
        return report

    monkeypatch.setattr("aevryn.cli.postgresql_audit_access_report", fake_access_report)

    with pytest.raises(ValueError, match=expected_error):
        _run_audit_access_verify(database_url="postgresql://example.invalid/aevryn")


def test_performance_baseline_help_describes_local_artifact(
    capsys: CaptureFixture[str],
) -> None:
    """Performance baseline help should describe the local ignored artifact."""
    with pytest.raises(SystemExit) as error:
        main(["performance-baseline", "--help"])
    output = capsys.readouterr().out

    assert error.value.code == 0
    assert "metadata-only Phase 9 performance baseline" in output
    assert "performance-baselines/latest.json" in output


def test_performance_baseline_command_writes_metadata_only_artifact(
    capsys: CaptureFixture[str],
) -> None:
    """Performance baseline command should write ignored metadata-only JSON."""
    output_path = Path("build") / "test_cli_performance" / "baseline.json"
    shutil.rmtree(output_path.parent, ignore_errors=True)

    exit_code = main(["performance-baseline", "--output", str(output_path)])
    captured = capsys.readouterr()
    artifact = json.loads(output_path.read_text(encoding="utf-8"))
    artifact_text = json.dumps(artifact, sort_keys=True)
    benchmark_names = {
        measurement["benchmark"]
        for measurement in artifact["snapshot"]["measurements"]
    }

    assert exit_code == 0
    assert f"Performance baseline written: {output_path}" in captured.out
    assert artifact["artifact_kind"] == "aevryn_phase9_performance_baseline"
    assert benchmark_names == {
        "export_preview",
        "import_inspect",
        "import_save",
        "project_status",
        "snapshot_creation",
        "validation_suite",
        "worker_processing",
        "workspace_load",
    }
    assert "Mark carried a rusty dagger" not in artifact_text
    assert "serialized_output" not in artifact_text
    assert "session_token" not in artifact_text


def test_performance_baseline_compare_passes_without_regressions(
    capsys: CaptureFixture[str],
    monkeypatch: MonkeyPatch,
) -> None:
    """Performance baseline comparison should pass when no regressions are found."""
    previous_path = Path("build") / "test_cli_performance" / "previous.json"

    monkeypatch.setattr(
        "aevryn.cli.compare_local_v2_performance_baseline",
        lambda path: [],
    )

    exit_code = main(["performance-baseline", "--compare-to", str(previous_path)])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Performance baseline comparison passed." in output


def test_performance_baseline_compare_fails_on_critical_regression(
    capsys: CaptureFixture[str],
    monkeypatch: MonkeyPatch,
) -> None:
    """Performance baseline comparison should fail only for critical regressions."""
    previous_path = Path("build") / "test_cli_performance" / "previous.json"

    monkeypatch.setattr(
        "aevryn.cli.compare_local_v2_performance_baseline",
        lambda path: [
            {
                "benchmark": "import_inspect",
                "previous_ms": 145.0,
                "current_ms": 920.0,
                "delta_ms": 775.0,
                "ratio": 6.345,
                "status": "critical",
            }
        ],
    )

    exit_code = main(["performance-baseline", "--compare-to", str(previous_path)])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "Performance regressions detected:" in output
    assert "critical import_inspect 145.0ms -> 920.0ms" in output


def test_performance_baseline_compare_reports_warning_without_failure(
    capsys: CaptureFixture[str],
    monkeypatch: MonkeyPatch,
) -> None:
    """Performance baseline comparison should report warning regressions but pass."""
    previous_path = Path("build") / "test_cli_performance" / "previous.json"

    monkeypatch.setattr(
        "aevryn.cli.compare_local_v2_performance_baseline",
        lambda path: [
            {
                "benchmark": "project_status",
                "previous_ms": 120.0,
                "current_ms": 260.0,
                "delta_ms": 140.0,
                "ratio": 2.167,
                "status": "warning",
            }
        ],
    )

    exit_code = main(["performance-baseline", "--compare-to", str(previous_path)])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Performance regressions detected:" in output
    assert "warning project_status 120.0ms -> 260.0ms" in output


def test_api_command_runs_configured_server(monkeypatch: MonkeyPatch) -> None:
    """API command should create the app and pass server options to Uvicorn."""
    captured: dict[str, object] = {}

    def fake_run_api_server(
        app: object,
        host: str,
        port: int,
        reload: bool,
        factory: bool = False,
    ) -> None:
        captured["app"] = app
        captured["host"] = host
        captured["port"] = port
        captured["reload"] = reload
        captured["factory"] = factory

    monkeypatch.setattr("aevryn.cli._run_api_server", fake_run_api_server)

    exit_code = main(
        [
            "api",
            "--host",
            "0.0.0.0",
            "--port",
            "9000",
            "--allowed-origin",
            "http://localhost:5173",
            "--reload",
        ]
    )

    assert exit_code == 0
    assert captured["host"] == "0.0.0.0"
    assert captured["port"] == 9000
    assert captured["reload"] is True
    assert captured["factory"] is True
    assert captured["app"] == "aevryn.api.app:create_app_from_env"


def test_api_command_passes_app_object_without_reload(monkeypatch: MonkeyPatch) -> None:
    """API command should pass a concrete app object when reload is disabled."""
    captured: dict[str, object] = {}
    monkeypatch.delenv("AEVRYN_API_ALLOWED_ORIGINS", raising=False)

    def fake_run_api_server(
        app: object,
        host: str,
        port: int,
        reload: bool,
        factory: bool = False,
    ) -> None:
        captured["app"] = app
        captured["host"] = host
        captured["port"] = port
        captured["reload"] = reload
        captured["factory"] = factory

    monkeypatch.setattr("aevryn.cli._run_api_server", fake_run_api_server)

    exit_code = main(["api", "--allowed-origin", "http://localhost:5173"])

    assert exit_code == 0
    assert captured["host"] == "127.0.0.1"
    assert captured["port"] == 8000
    assert captured["reload"] is False
    assert captured["factory"] is False
    assert captured["app"] != "aevryn.api.app:create_app_from_env"
    assert "AEVRYN_API_ALLOWED_ORIGINS" not in os.environ


def ai_response_file(anchor_id: str) -> Path:
    """Create an evidence-bounded AI JSON response file."""
    path = Path("build") / "test_cli" / "ai_response.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "entities": [
                    {
                        "entity_id": "character_mark",
                        "entity_type": "character",
                        "display_name": "Mark",
                        "evidence_anchor_id": anchor_id,
                        "confidence": 0.95,
                    },
                    {
                        "entity_id": "item_iron_sword",
                        "entity_type": "item",
                        "display_name": "Iron Sword",
                        "evidence_anchor_id": anchor_id,
                        "confidence": 0.9,
                    },
                ],
                "facts": [
                    {
                        "fact_id": "fact_character_mark_current_weapon_iron_sword",
                        "entity_id": "character_mark",
                        "attribute": "current_weapon",
                        "value": "Iron Sword",
                        "evidence_anchor_id": anchor_id,
                        "confidence": 0.9,
                    }
                ],
                "relationships": [
                    {
                        "source_entity_id": "character_mark",
                        "relationship_type": "owns",
                        "target_entity_id": "item_iron_sword",
                        "evidence_anchor_id": anchor_id,
                        "confidence": 0.85,
                    }
                ],
                "state_changes": [
                    {
                        "entity_id": "character_mark",
                        "attribute": "current_weapon",
                        "value": "Iron Sword",
                        "valid_from_anchor_id": anchor_id,
                        "confidence": 0.9,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def luna_ai_response_file(anchor_id: str) -> Path:
    """Create an evidence-bounded AI JSON response for a non-demo character."""
    path = Path("build") / "test_cli" / "luna_ai_response.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "entities": [
                    {
                        "entity_id": "character_luna",
                        "entity_type": "character",
                        "display_name": "Luna",
                        "evidence_anchor_id": anchor_id,
                        "confidence": 0.95,
                    }
                ],
                "facts": [
                    {
                        "fact_id": "fact_character_luna_current_goal_investigate",
                        "entity_id": "character_luna",
                        "attribute": "current_goal",
                        "value": "Investigate the scene",
                        "evidence_anchor_id": anchor_id,
                        "confidence": 0.9,
                    }
                ],
                "relationships": [],
                "state_changes": [
                    {
                        "entity_id": "character_luna",
                        "attribute": "current_goal",
                        "value": "Investigate the scene",
                        "valid_from_anchor_id": anchor_id,
                        "valid_until_anchor_id": None,
                        "confidence": 0.9,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def multi_scene_ai_response_file() -> Path:
    """Create a multi-scene evidence-bounded AI JSON response file."""
    path = Path("build") / "test_cli" / "multi_scene_ai_response.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "scenes": {
                    "demo_chapter_001_scene_001": weapon_payload(
                        anchor_id=(
                            "demo_chapter_001_scene_001_paragraph_001_"
                            "sentence_001_anchor"
                        ),
                        weapon="Rusty Dagger",
                    ),
                    "demo_chapter_002_scene_001": weapon_payload(
                        anchor_id=(
                            "demo_chapter_002_scene_001_paragraph_001_"
                            "sentence_001_anchor"
                        ),
                        weapon="Iron Sword",
                    ),
                }
            }
        ),
        encoding="utf-8",
    )
    return path


def scene_position_ai_response_file() -> Path:
    """Create multi-scene AI JSON for scene-position CLI view tests."""
    path = Path("build") / "test_cli" / "scene_position_ai_response.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "scenes": {
                    "demo_chapter_001_scene_001": {
                        "entities": [
                            {
                                "entity_id": "character_mark",
                                "entity_type": "character",
                                "display_name": "Mark",
                                "evidence_anchor_id": (
                                    "demo_chapter_001_scene_001_paragraph_001_"
                                    "sentence_001_anchor"
                                ),
                                "confidence": 0.95,
                            },
                            {
                                "entity_id": "location_hangar",
                                "entity_type": "location",
                                "display_name": "Hangar",
                                "evidence_anchor_id": (
                                    "demo_chapter_001_scene_001_paragraph_001_"
                                    "sentence_001_anchor"
                                ),
                                "confidence": 0.95,
                            },
                        ],
                        "facts": [
                            {
                                "fact_id": "fact_mark_mood_calm",
                                "entity_id": "character_mark",
                                "attribute": "current_mood",
                                "value": "Calm",
                                "evidence_anchor_id": (
                                    "demo_chapter_001_scene_001_paragraph_001_"
                                    "sentence_001_anchor"
                                ),
                                "confidence": 0.95,
                            },
                            {
                                "fact_id": "fact_hangar_condition_quiet",
                                "entity_id": "location_hangar",
                                "attribute": "condition",
                                "value": "Quiet",
                                "evidence_anchor_id": (
                                    "demo_chapter_001_scene_001_paragraph_001_"
                                    "sentence_001_anchor"
                                ),
                                "confidence": 0.95,
                            },
                        ],
                        "relationships": [],
                        "state_changes": [],
                    },
                    "demo_chapter_001_scene_002": {
                        "entities": [
                            {
                                "entity_id": "character_mark",
                                "entity_type": "character",
                                "display_name": "Mark",
                                "evidence_anchor_id": (
                                    "demo_chapter_001_scene_002_paragraph_001_"
                                    "sentence_001_anchor"
                                ),
                                "confidence": 0.95,
                            },
                            {
                                "entity_id": "location_hangar",
                                "entity_type": "location",
                                "display_name": "Hangar",
                                "evidence_anchor_id": (
                                    "demo_chapter_001_scene_002_paragraph_001_"
                                    "sentence_001_anchor"
                                ),
                                "confidence": 0.95,
                            },
                        ],
                        "facts": [
                            {
                                "fact_id": "fact_mark_mood_alarmed",
                                "entity_id": "character_mark",
                                "attribute": "current_mood",
                                "value": "Alarmed",
                                "evidence_anchor_id": (
                                    "demo_chapter_001_scene_002_paragraph_001_"
                                    "sentence_001_anchor"
                                ),
                                "confidence": 0.95,
                            },
                            {
                                "fact_id": "fact_hangar_condition_alarm",
                                "entity_id": "location_hangar",
                                "attribute": "condition",
                                "value": "Alarm active",
                                "evidence_anchor_id": (
                                    "demo_chapter_001_scene_002_paragraph_001_"
                                    "sentence_001_anchor"
                                ),
                                "confidence": 0.95,
                            },
                        ],
                        "relationships": [],
                        "state_changes": [],
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    return path


def test_import_command_prints_source_counts(capsys: CaptureFixture[str]) -> None:
    """Import prints stable source structure counts."""
    path = source_file()

    exit_code = main(["import", str(path), "--source-id", "demo", "--title", "Demo"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert '"chapters": 2' in output
    assert '"evidence_anchors": 2' in output


def test_import_command_prints_chapter_and_scene_ids(
    capsys: CaptureFixture[str],
) -> None:
    """Import output should expose IDs users need for later commands."""
    path = source_file()

    exit_code = main(["import", str(path), "--source-id", "demo", "--title", "Demo"])
    output = capsys.readouterr().out
    imported = json.loads(output)

    assert exit_code == 0
    assert imported["chapter_ids"] == [
        "demo_chapter_001",
        "demo_chapter_002",
    ]
    assert imported["source_format"] == "txt"
    assert imported["scene_ids"] == [
        "demo_chapter_001_scene_001",
        "demo_chapter_002_scene_001",
    ]
    assert imported["scene_map"] == [
        {
            "chapter_id": "demo_chapter_001",
            "chapter_index": 1,
            "scene_id": "demo_chapter_001_scene_001",
            "scene_index": 1,
            "title": "Scene 1",
        },
        {
            "chapter_id": "demo_chapter_002",
            "chapter_index": 2,
            "scene_id": "demo_chapter_002_scene_001",
            "scene_index": 1,
            "title": "Scene 1",
        },
    ]
    assert imported["first_evidence_anchors"] == [
        {
            "anchor_id": "demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor",
            "chapter_id": "demo_chapter_001",
            "scene_id": "demo_chapter_001_scene_001",
            "paragraph_index": 1,
            "sentence_index": 1,
        },
        {
            "anchor_id": "demo_chapter_002_scene_001_paragraph_001_sentence_001_anchor",
            "chapter_id": "demo_chapter_002",
            "scene_id": "demo_chapter_002_scene_001",
            "paragraph_index": 1,
            "sentence_index": 1,
        },
    ]


def test_cli_reports_missing_file_without_traceback(
    capsys: CaptureFixture[str],
) -> None:
    """CLI reports expected file errors with a nonzero exit code."""
    exit_code = main(["import", "build/test_cli/missing.txt", "--source-id", "demo"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "Error: File not found:" in captured.err
    assert "build/test_cli/missing.txt" in captured.err.replace("\\", "/")


def test_import_command_rejects_out_of_order_chapters(
    capsys: CaptureFixture[str],
) -> None:
    """Import reports out-of-order chapters without a traceback."""
    path = out_of_order_source_file()

    exit_code = main(["import", str(path), "--source-id", "demo"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "increasing order" in captured.err


def test_extract_demo_command_prints_candidates(capsys: CaptureFixture[str]) -> None:
    """Demo extraction prints accepted candidate counts."""
    path = source_file()

    exit_code = main(["extract-demo", str(path), "--source-id", "demo"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert '"entity_id": "character_mark"' in output
    assert '"accepted_relationships": 2' in output


def test_character_command_prints_character_sheet(capsys: CaptureFixture[str]) -> None:
    """Character command prints a canon-backed character sheet."""
    path = source_file()

    exit_code = main(["character", str(path), "--source-id", "demo"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "# Mark" in output
    assert "## Current Equipment" in output
    assert "- Iron Sword" in output
    assert "## Evidence" in output


def test_scene_command_reports_unknown_scene(
    capsys: CaptureFixture[str],
) -> None:
    """CLI returns a clean error for unknown scene requests."""
    path = source_file()

    exit_code = main(
        [
            "scene",
            str(path),
            "--source-id",
            "demo",
            "--scene-id",
            "missing_scene",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "Unknown scene" in captured.err
    assert "aevryn import <path> --source-id <id>" in captured.err


def test_character_command_reports_unknown_character_with_hint(
    capsys: CaptureFixture[str],
) -> None:
    """CLI helps users recover from unknown character selections."""
    path = source_file()

    exit_code = main(
        [
            "character",
            str(path),
            "--source-id",
            "demo",
            "--character-id",
            "character_missing",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "Unknown character: character_missing" in captured.err
    assert "accepted_entity_ids" in captured.err


def test_scene_command_prints_scene_sheet(capsys: CaptureFixture[str]) -> None:
    """Scene command prints a canon-backed scene sheet."""
    path = source_file()

    exit_code = main(["scene", str(path), "--source-id", "demo"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "# Scene 1" in output
    assert "## Characters Present" in output
    assert "- Mark" in output
    assert "## Continuity Changes" in output


def test_scene_command_defaults_to_accepted_scene_characters(
    capsys: CaptureFixture[str],
) -> None:
    """Scene command should not default to demo character IDs for real stories."""
    path = single_scene_source_file()
    response_path = luna_ai_response_file(
        "demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor"
    )

    exit_code = main(
        [
            "scene",
            str(path),
            "--source-id",
            "demo",
            "--ai-response-file",
            str(response_path),
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "- Luna" in output
    assert "character_mark" not in output


def test_scene_command_dedupes_repeated_character_ids(
    capsys: CaptureFixture[str],
) -> None:
    """CLI does not duplicate scene participants from repeated flags."""
    path = source_file()

    exit_code = main(
        [
            "scene",
            str(path),
            "--source-id",
            "demo",
            "--character-id",
            "character_mark",
            "--character-id",
            "character_mark",
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "## Characters Present\n- Mark" in output
    characters_section = output.split("## Characters Present", maxsplit=1)[1].split(
        "## Mood",
        maxsplit=1,
    )[0]
    assert characters_section.count("- Mark") == 1


def test_scene_command_rejects_invalid_character_id(
    capsys: CaptureFixture[str],
) -> None:
    """CLI selected character IDs must be machine-safe."""
    path = source_file()

    exit_code = main(
        [
            "scene",
            str(path),
            "--source-id",
            "demo",
            "--character-id",
            "character mark",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "Selected entity ID cannot contain whitespace" in captured.err


def test_prompt_command_prints_prompt_sheet(capsys: CaptureFixture[str]) -> None:
    """Prompt command prints deterministic prompts from scene context."""
    path = source_file()

    exit_code = main(["prompt", str(path), "--source-id", "demo"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "## Image Prompt" in output
    assert "Narrate using only accepted canon facts." in output


def test_extraction_prompt_command_prints_anchor_bounded_prompt(
    capsys: CaptureFixture[str],
) -> None:
    """Extraction prompt command prints scene text and allowed anchors."""
    path = single_scene_source_file()

    exit_code = main(["extraction-prompt", str(path), "--source-id", "demo"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Use only the provided evidence anchors." in output
    assert "demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor" in output


def test_extraction_prompt_command_prints_utf8_story_text(
    capsys: CaptureFixture[str],
) -> None:
    """Extraction prompt command preserves UTF-8 story text."""
    path = unicode_source_file()

    exit_code = main(["extraction-prompt", str(path), "--source-id", "demo"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "【Entry】" in output
    assert "fiancée" in output


def test_extract_ai_json_command_prints_acceptance_summary(
    capsys: CaptureFixture[str],
) -> None:
    """AI JSON extraction command applies candidates through Canon Updating."""
    path = single_scene_source_file()
    response_path = ai_response_file(
        "demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor"
    )

    exit_code = main(
        ["extract-ai-json", str(path), str(response_path), "--source-id", "demo"]
    )
    output = capsys.readouterr().out
    summary = json.loads(output)

    assert exit_code == 0
    assert summary["accepted_facts"] == 3
    assert summary["accepted_relationships"] == 1
    assert summary["accepted_entity_ids"] == [
        "character_mark",
        "item_iron_sword",
    ]
    assert summary["accepted_relationship_ids"] == [
        "relationship_character_mark_owns_item_iron_sword"
    ]
    assert summary["rejected_candidate_ids"] == []


def test_extract_ai_json_command_can_apply_multi_scene_payloads(
    capsys: CaptureFixture[str],
) -> None:
    """AI JSON command can apply a scene-keyed response envelope."""
    path = source_file()
    response_path = multi_scene_ai_response_file()

    exit_code = main(
        ["extract-ai-json", str(path), str(response_path), "--source-id", "demo"]
    )
    output = capsys.readouterr().out
    summary = json.loads(output)

    assert exit_code == 0
    assert [
        result["scene_id"] for result in summary["results"]
    ] == [
        "demo_chapter_001_scene_001",
        "demo_chapter_002_scene_001",
    ]
    assert summary["accepted_facts"] == 3
    assert summary["accepted_entity_ids"] == ["character_mark"]


def test_extract_ai_json_command_can_apply_multi_scene_payload_list(
    capsys: CaptureFixture[str],
) -> None:
    """AI JSON command can apply a list-form multi-scene response envelope."""
    path = source_file()
    response_path = Path("build") / "test_cli" / "multi_scene_ai_response_list.json"
    response_path.write_text(
        json.dumps(
            {
                "scenes": [
                    {
                        "scene_id": "demo_chapter_001_scene_001",
                        **weapon_payload(
                            anchor_id=(
                                "demo_chapter_001_scene_001_paragraph_001_"
                                "sentence_001_anchor"
                            ),
                            weapon="Rusty Dagger",
                        ),
                    },
                    {
                        "scene_id": "demo_chapter_002_scene_001",
                        **weapon_payload(
                            anchor_id=(
                                "demo_chapter_002_scene_001_paragraph_001_"
                                "sentence_001_anchor"
                            ),
                            weapon="Iron Sword",
                        ),
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        ["extract-ai-json", str(path), str(response_path), "--source-id", "demo"]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert '"scene_id": "demo_chapter_001_scene_001"' in output
    assert '"scene_id": "demo_chapter_002_scene_001"' in output


def test_extract_ai_json_command_rejects_unknown_multi_scene_payload(
    capsys: CaptureFixture[str],
) -> None:
    """AI JSON command rejects scene payloads outside the imported source."""
    path = source_file()
    response_path = Path("build") / "test_cli" / "unknown_scene_ai_response.json"
    response_path.write_text(
        json.dumps(
            {
                "scenes": {
                    "demo_chapter_001_scene_001": weapon_payload(
                        anchor_id=(
                            "demo_chapter_001_scene_001_paragraph_001_"
                            "sentence_001_anchor"
                        ),
                        weapon="Rusty Dagger",
                    ),
                    "demo_chapter_999_scene_001": weapon_payload(
                        anchor_id=(
                            "demo_chapter_001_scene_001_paragraph_001_"
                            "sentence_001_anchor"
                        ),
                        weapon="Future Sword",
                    ),
                }
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        ["extract-ai-json", str(path), str(response_path), "--source-id", "demo"]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "unknown scenes" in captured.err


def test_extract_ai_json_command_rejects_duplicate_list_scene_payloads(
    capsys: CaptureFixture[str],
) -> None:
    """AI JSON command rejects duplicate scene IDs in list-form envelopes."""
    path = source_file()
    response_path = Path("build") / "test_cli" / "duplicate_scene_ai_response.json"
    response_path.write_text(
        json.dumps(
            {
                "scenes": [
                    {
                        "scene_id": "demo_chapter_001_scene_001",
                        **weapon_payload(
                            anchor_id=(
                                "demo_chapter_001_scene_001_paragraph_001_"
                                "sentence_001_anchor"
                            ),
                            weapon="Rusty Dagger",
                        ),
                    },
                    {
                        "scene_id": "demo_chapter_001_scene_001",
                        **weapon_payload(
                            anchor_id=(
                                "demo_chapter_001_scene_001_paragraph_001_"
                                "sentence_001_anchor"
                            ),
                            weapon="Iron Sword",
                        ),
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        ["extract-ai-json", str(path), str(response_path), "--source-id", "demo"]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "duplicate scene" in captured.err


def test_extract_ai_json_command_rejects_extra_multi_scene_envelope_keys(
    capsys: CaptureFixture[str],
) -> None:
    """AI JSON command rejects unsupported multi-scene envelope fields."""
    path = source_file()
    response_path = Path("build") / "test_cli" / "extra_envelope_ai_response.json"
    response_path.write_text(
        json.dumps(
            {
                "scenes": {
                    "demo_chapter_001_scene_001": weapon_payload(
                        anchor_id=(
                            "demo_chapter_001_scene_001_paragraph_001_"
                            "sentence_001_anchor"
                        ),
                        weapon="Rusty Dagger",
                    ),
                    "demo_chapter_002_scene_001": weapon_payload(
                        anchor_id=(
                            "demo_chapter_002_scene_001_paragraph_001_"
                            "sentence_001_anchor"
                        ),
                        weapon="Iron Sword",
                    ),
                },
                "summary": "unsupported",
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        ["extract-ai-json", str(path), str(response_path), "--source-id", "demo"]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "unsupported envelope keys" in captured.err


def test_extract_ai_json_command_rejects_duplicate_multi_scene_keys(
    capsys: CaptureFixture[str],
) -> None:
    """AI JSON command rejects duplicate JSON object keys in envelopes."""
    path = source_file()
    response_path = Path("build") / "test_cli" / "duplicate_key_ai_response.json"
    response_path.write_text(
        (
            '{"scenes": {"demo_chapter_001_scene_001": '
            '{"entities": [], "facts": [], "relationships": [], "state_changes": []}, '
            '"demo_chapter_001_scene_001": '
            '{"entities": [], "facts": [], "relationships": [], "state_changes": []}}}'
        ),
        encoding="utf-8",
    )

    exit_code = main(
        ["extract-ai-json", str(path), str(response_path), "--source-id", "demo"]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "duplicate key" in captured.err


def test_extract_ai_json_command_rejects_blank_multi_scene_id(
    capsys: CaptureFixture[str],
) -> None:
    """AI JSON command rejects blank object-form scene IDs."""
    path = source_file()
    response_path = Path("build") / "test_cli" / "blank_scene_id_ai_response.json"
    response_path.write_text(
        json.dumps(
            {
                "scenes": {
                    "": weapon_payload(
                        anchor_id=(
                            "demo_chapter_001_scene_001_paragraph_001_"
                            "sentence_001_anchor"
                        ),
                        weapon="Rusty Dagger",
                    )
                }
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        ["extract-ai-json", str(path), str(response_path), "--source-id", "demo"]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "AI multi-scene response scene ID is required" in captured.err


def test_extract_ai_json_command_rejects_whitespace_multi_scene_id(
    capsys: CaptureFixture[str],
) -> None:
    """AI JSON command rejects list-form scene IDs that are not machine-safe."""
    path = source_file()
    response_path = Path("build") / "test_cli" / "whitespace_scene_id_ai_response.json"
    response_path.write_text(
        json.dumps(
            {
                "scenes": [
                    {
                        "scene_id": "demo chapter 001 scene 001",
                        **weapon_payload(
                            anchor_id=(
                                "demo_chapter_001_scene_001_paragraph_001_"
                                "sentence_001_anchor"
                            ),
                            weapon="Rusty Dagger",
                        ),
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        ["extract-ai-json", str(path), str(response_path), "--source-id", "demo"]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "AI multi-scene response scene ID cannot contain whitespace" in captured.err


def test_prompt_command_can_use_ai_json_candidates(
    capsys: CaptureFixture[str],
) -> None:
    """Prompt command can use evidence-bounded AI JSON candidates."""
    path = single_scene_source_file()
    response_path = ai_response_file(
        "demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor"
    )

    exit_code = main(
        [
            "prompt",
            str(path),
            "--source-id",
            "demo",
            "--ai-response-file",
            str(response_path),
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Mark retains Current Weapon: Iron Sword" in output
    assert "character_mark retains current_weapon" not in output


def test_prompt_command_defaults_to_accepted_scene_characters(
    capsys: CaptureFixture[str],
) -> None:
    """Prompt command should use accepted scene characters when none are selected."""
    path = single_scene_source_file()
    response_path = luna_ai_response_file(
        "demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor"
    )

    exit_code = main(
        [
            "prompt",
            str(path),
            "--source-id",
            "demo",
            "--ai-response-file",
            str(response_path),
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Luna" in output
    assert "character_mark" not in output


def test_character_command_can_use_ai_json_scene_id(
    capsys: CaptureFixture[str],
) -> None:
    """Character command can apply scene-specific AI JSON candidates."""
    path = single_scene_source_file()
    response_path = ai_response_file(
        "demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor"
    )

    exit_code = main(
        [
            "character",
            str(path),
            "--source-id",
            "demo",
            "--character-id",
            "character_mark",
            "--scene-id",
            "demo_chapter_001_scene_001",
            "--ai-response-file",
            str(response_path),
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "## Current Equipment" in output
    assert "- Iron Sword" in output


def test_character_command_uses_scene_id_for_final_view(
    capsys: CaptureFixture[str],
) -> None:
    """Character command scene ID controls the reconstructed card position."""
    path = two_scene_source_file()
    response_path = scene_position_ai_response_file()

    first_exit_code = main(
        [
            "character",
            str(path),
            "--source-id",
            "demo",
            "--character-id",
            "character_mark",
            "--scene-id",
            "demo_chapter_001_scene_001",
            "--ai-response-file",
            str(response_path),
        ]
    )
    first_output = capsys.readouterr().out
    second_exit_code = main(
        [
            "character",
            str(path),
            "--source-id",
            "demo",
            "--character-id",
            "character_mark",
            "--scene-id",
            "demo_chapter_001_scene_002",
            "--ai-response-file",
            str(response_path),
        ]
    )
    second_output = capsys.readouterr().out

    assert first_exit_code == 0
    assert second_exit_code == 0
    assert "current_mood -> Calm" in first_output
    assert "current_mood -> Alarmed" in second_output


def test_world_command_can_use_ai_json_candidates(
    capsys: CaptureFixture[str],
) -> None:
    """World command prints a presented world sheet from accepted candidates."""
    path = single_scene_source_file()
    response_path = ai_response_file(
        "demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor"
    )

    exit_code = main(
        [
            "world",
            str(path),
            "--source-id",
            "demo",
            "--entity-id",
            "item_iron_sword",
            "--ai-response-file",
            str(response_path),
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "# World Sheet" in output
    assert "Iron Sword (item)" in output


def test_world_command_can_print_json(capsys: CaptureFixture[str]) -> None:
    """World command can print machine-readable world state JSON."""
    path = single_scene_source_file()
    response_path = ai_response_file(
        "demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor"
    )

    exit_code = main(
        [
            "world",
            str(path),
            "--source-id",
            "demo",
            "--entity-id",
            "item_iron_sword",
            "--ai-response-file",
            str(response_path),
            "--format",
            "json",
        ]
    )
    output = capsys.readouterr().out
    exported = json.loads(output)

    assert exit_code == 0
    assert exported["entities"][0]["entity_id"] == "item_iron_sword"
    assert exported["entities"][0]["facts"][0]["evidence"]["quote"] == (
        "Mark bought an iron sword."
    )


def test_world_command_uses_scene_id_for_final_view(
    capsys: CaptureFixture[str],
) -> None:
    """World command scene ID controls the reconstructed world position."""
    path = two_scene_source_file()
    response_path = scene_position_ai_response_file()

    first_exit_code = main(
        [
            "world",
            str(path),
            "--source-id",
            "demo",
            "--entity-id",
            "location_hangar",
            "--scene-id",
            "demo_chapter_001_scene_001",
            "--ai-response-file",
            str(response_path),
        ]
    )
    first_output = capsys.readouterr().out
    second_exit_code = main(
        [
            "world",
            str(path),
            "--source-id",
            "demo",
            "--entity-id",
            "location_hangar",
            "--scene-id",
            "demo_chapter_001_scene_002",
            "--ai-response-file",
            str(response_path),
        ]
    )
    second_output = capsys.readouterr().out

    assert first_exit_code == 0
    assert second_exit_code == 0
    assert "condition: Quiet" in first_output
    assert "condition: Alarm active" in second_output


def test_world_command_dedupes_repeated_entity_ids(
    capsys: CaptureFixture[str],
) -> None:
    """CLI world command dedupes repeated selected entities."""
    path = single_scene_source_file()
    response_path = ai_response_file(
        "demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor"
    )

    exit_code = main(
        [
            "world",
            str(path),
            "--source-id",
            "demo",
            "--entity-id",
            "item_iron_sword",
            "--entity-id",
            "item_iron_sword",
            "--ai-response-file",
            str(response_path),
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert output.count("Iron Sword (item)") == 1


def test_world_command_reports_unknown_entity_with_hint(
    capsys: CaptureFixture[str],
) -> None:
    """CLI helps users recover from unknown world entity selections."""
    path = single_scene_source_file()
    response_path = ai_response_file(
        "demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor"
    )

    exit_code = main(
        [
            "world",
            str(path),
            "--source-id",
            "demo",
            "--entity-id",
            "item_missing",
            "--ai-response-file",
            str(response_path),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "Unknown world entity: item_missing" in captured.err
    assert "accepted entity ID" in captured.err


def test_continuity_command_prints_report(capsys: CaptureFixture[str]) -> None:
    """Continuity command prints a human-readable continuity report."""
    path = source_file()

    exit_code = main(["continuity", str(path), "--source-id", "demo"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "# Continuity Report: demo" in output
    assert "### New" in output
    assert "### Still Known" in output


def test_continuity_command_can_print_json(capsys: CaptureFixture[str]) -> None:
    """Continuity command can print machine-readable report JSON."""
    path = source_file()

    exit_code = main(
        ["continuity", str(path), "--source-id", "demo", "--format", "json"]
    )
    output = capsys.readouterr().out
    exported = json.loads(output)

    assert exit_code == 0
    assert exported["source_id"] == "demo"
    assert exported["scenes"]


def test_continuity_command_can_use_multi_scene_ai_payloads(
    capsys: CaptureFixture[str],
) -> None:
    """Continuity command can report changes from a multi-scene AI envelope."""
    path = source_file()
    response_path = multi_scene_ai_response_file()

    exit_code = main(
        [
            "continuity",
            str(path),
            "--source-id",
            "demo",
            "--ai-response-file",
            str(response_path),
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "character_mark current_weapon = Iron Sword" in output
    assert "character_mark current_weapon = Rusty Dagger" in output


def test_validate_command_runs_local_validation_suite(capsys: CaptureFixture[str]) -> None:
    """Validate command runs local corpus metadata against local chapter files."""
    source_root = Path("build") / "test_cli_validate" / "sources"
    source_dir = source_root / "Demo Genre"
    case_dir = Path("build") / "test_cli_validate" / "cases"
    source_dir.mkdir(parents=True, exist_ok=True)
    case_dir.mkdir(parents=True, exist_ok=True)
    for existing_case in case_dir.glob("*.json"):
        existing_case.unlink()
    (source_dir / "Demo Chapter 1.txt").write_text(
        "Chapter 1\nMark found a brass key.",
        encoding="utf-8",
    )
    (source_dir / "Demo Chapter 2.txt").write_text(
        "Chapter 2\nMark opened the archive.",
        encoding="utf-8",
    )
    (case_dir / "demo_validation_case.json").write_text(
        json.dumps(
            {
                "case_id": "demo_validation_case",
                "title": "Demo",
                "genre": "Demo",
                "source_directory": "Demo Genre",
                "chapter_glob": "*.txt",
                "expected_import": _cli_validation_expected_import(source_dir),
                "expected_extraction": _cli_validation_expected_extraction(source_dir),
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "validate",
            "--case-dir",
            str(case_dir),
            "--source-root",
            str(source_root),
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Demo - Demo" in output
    assert "PASS" in output
    assert "files=2 chapters=2 scenes=2 paragraphs=2 sentences=2 anchors=2" in output
    assert "extraction_inputs=2 extraction_anchors=2" in output
    assert (
        "cases=1 passed=1 failed=0 files=2 chapters=2 scenes=2 "
        "paragraphs=2 sentences=2 anchors=2 extraction_inputs=2 "
        "extraction_anchors=2"
    ) in output
    assert "Validation Digest" in output
    assert "100%" in output


def test_validate_command_uses_environment_source_root(
    capsys: CaptureFixture[str],
    monkeypatch: MonkeyPatch,
) -> None:
    """Validate command uses AEVRYN_VALIDATION_ROOT when no source root is passed."""
    source_root = Path("build") / "test_cli_validate_env" / "sources"
    source_dir = source_root / "Demo Genre"
    case_dir = Path("build") / "test_cli_validate_env" / "cases"
    source_dir.mkdir(parents=True, exist_ok=True)
    case_dir.mkdir(parents=True, exist_ok=True)
    for existing_case in case_dir.glob("*.json"):
        existing_case.unlink()
    (source_dir / "Demo Chapter 1.txt").write_text(
        "Chapter 1\nMark found a brass key.",
        encoding="utf-8",
    )
    (source_dir / "Demo Chapter 2.txt").write_text(
        "Chapter 2\nMark opened the archive.",
        encoding="utf-8",
    )
    (case_dir / "demo_validation_case.json").write_text(
        json.dumps(
            {
                "case_id": "demo_validation_case",
                "title": "Demo",
                "genre": "Demo",
                "source_directory": "Demo Genre",
                "chapter_glob": "*.txt",
                "expected_import": _cli_validation_expected_import(source_dir),
                "expected_extraction": _cli_validation_expected_extraction(source_dir),
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("AEVRYN_VALIDATION_ROOT", str(source_root))

    exit_code = main(["validate", "--case-dir", str(case_dir)])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Demo - Demo" in output
    assert "cases=1 passed=1 failed=0" in output


def test_validate_source_root_argument_overrides_environment(
    capsys: CaptureFixture[str],
    monkeypatch: MonkeyPatch,
) -> None:
    """Validate --source-root has priority over AEVRYN_VALIDATION_ROOT."""
    source_root = Path("build") / "test_cli_validate_arg_over_env" / "sources"
    source_dir = source_root / "Demo Genre"
    env_root = Path("build") / "test_cli_validate_arg_over_env" / "wrong_sources"
    case_dir = Path("build") / "test_cli_validate_arg_over_env" / "cases"
    source_dir.mkdir(parents=True, exist_ok=True)
    env_root.mkdir(parents=True, exist_ok=True)
    case_dir.mkdir(parents=True, exist_ok=True)
    for existing_case in case_dir.glob("*.json"):
        existing_case.unlink()
    (source_dir / "Demo Chapter 1.txt").write_text(
        "Chapter 1\nMark found a brass key.",
        encoding="utf-8",
    )
    (source_dir / "Demo Chapter 2.txt").write_text(
        "Chapter 2\nMark opened the archive.",
        encoding="utf-8",
    )
    (case_dir / "demo_validation_case.json").write_text(
        json.dumps(
            {
                "case_id": "demo_validation_case",
                "title": "Demo",
                "genre": "Demo",
                "source_directory": "Demo Genre",
                "chapter_glob": "*.txt",
                "expected_import": _cli_validation_expected_import(source_dir),
                "expected_extraction": _cli_validation_expected_extraction(source_dir),
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("AEVRYN_VALIDATION_ROOT", str(env_root))

    exit_code = main(
        [
            "validate",
            "--case-dir",
            str(case_dir),
            "--source-root",
            str(source_root),
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Demo - Demo" in output
    assert "cases=1 passed=1 failed=0" in output


def test_validate_rejects_blank_environment_source_root(
    capsys: CaptureFixture[str],
    monkeypatch: MonkeyPatch,
) -> None:
    """Validate command reports blank AEVRYN_VALIDATION_ROOT clearly."""
    case_dir = Path("build") / "test_cli_validate_blank_env" / "cases"
    case_dir.mkdir(parents=True, exist_ok=True)
    for existing_case in case_dir.glob("*.json"):
        existing_case.unlink()
    monkeypatch.setenv("AEVRYN_VALIDATION_ROOT", "   ")

    exit_code = main(["validate", "--case-dir", str(case_dir)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "AEVRYN_VALIDATION_ROOT cannot be blank." in captured.err


def test_validate_command_can_print_summary_only(capsys: CaptureFixture[str]) -> None:
    """Validate command can suppress per-case text for quick corpus checks."""
    source_root = Path("build") / "test_cli_validate_summary" / "sources"
    source_dir = source_root / "Demo Genre"
    case_dir = Path("build") / "test_cli_validate_summary" / "cases"
    source_dir.mkdir(parents=True, exist_ok=True)
    case_dir.mkdir(parents=True, exist_ok=True)
    for existing_case in case_dir.glob("*.json"):
        existing_case.unlink()
    (source_dir / "Demo Chapter 1.txt").write_text(
        "Chapter 1\nMark found a brass key.",
        encoding="utf-8",
    )
    (source_dir / "Demo Chapter 2.txt").write_text(
        "Chapter 2\nMark opened the archive.",
        encoding="utf-8",
    )
    (case_dir / "demo_validation_case.json").write_text(
        json.dumps(
            {
                "case_id": "demo_validation_case",
                "title": "Demo",
                "genre": "Demo",
                "source_directory": "Demo Genre",
                "chapter_glob": "*.txt",
                "expected_import": _cli_validation_expected_import(source_dir),
                "expected_extraction": _cli_validation_expected_extraction(source_dir),
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "validate",
            "--case-dir",
            str(case_dir),
            "--source-root",
            str(source_root),
            "--summary-only",
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Validation Summary" in output
    assert "Validation Totals" in output
    assert "Validation Digest" in output
    assert "Validation Score" in output
    assert "Demo - Demo" not in output
    assert "PASS" not in output
    assert (
        "cases=1 passed=1 failed=0 files=2 chapters=2 scenes=2 "
        "paragraphs=2 sentences=2 anchors=2 extraction_inputs=2 "
        "extraction_anchors=2"
    ) in output


def test_validate_command_can_print_json(capsys: CaptureFixture[str]) -> None:
    """Validate command can print machine-readable validation results."""
    source_root = Path("build") / "test_cli_validate_json" / "sources"
    source_dir = source_root / "Demo Genre"
    case_dir = Path("build") / "test_cli_validate_json" / "cases"
    source_dir.mkdir(parents=True, exist_ok=True)
    case_dir.mkdir(parents=True, exist_ok=True)
    for existing_case in case_dir.glob("*.json"):
        existing_case.unlink()
    (source_dir / "Demo Chapter 1.txt").write_text(
        "Chapter 1\nMark found a brass key.",
        encoding="utf-8",
    )
    (source_dir / "Demo Chapter 2.txt").write_text(
        "Chapter 2\nMark opened the archive.",
        encoding="utf-8",
    )
    (case_dir / "demo_validation_case.json").write_text(
        json.dumps(
            {
                "case_id": "demo_validation_case",
                "title": "Demo",
                "genre": "Demo",
                "source_directory": "Demo Genre",
                "chapter_glob": "*.txt",
                "expected_import": _cli_validation_expected_import(source_dir),
                "expected_extraction": _cli_validation_expected_extraction(source_dir),
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "validate",
            "--case-dir",
            str(case_dir),
            "--source-root",
            str(source_root),
            "--format",
            "json",
        ]
    )
    output = capsys.readouterr().out
    exported = json.loads(output)

    assert exit_code == 0
    assert exported["passed"] is True
    assert exported["score"] == 100
    assert re.fullmatch(r"[0-9a-f]{64}", exported["suite_digest"])
    assert exported["totals"]["cases"] == 1
    assert exported["totals"]["chapter_files"] == 2
    assert exported["totals"]["evidence_anchors"] == 2
    assert exported["totals"]["extraction_inputs"] == 2
    assert exported["totals"]["extraction_anchors"] == 2
    assert exported["results"][0]["actual_import"]["chapter_files"] == 2
    assert exported["results"][0]["actual_import"]["sentences"] == 2
    assert exported["results"][0]["actual_extraction"]["scene_inputs"] == 2
    assert re.fullmatch(
        r"[0-9a-f]{64}",
        exported["results"][0]["actual_extraction"]["extraction_prompt_digest"],
    )
    assert "Mark found a brass key." not in output
    assert "Mark opened the archive." not in output
    assert "Scene Text:" not in output
    assert "Evidence Anchors:" not in output


def test_validate_command_can_write_snapshot(capsys: CaptureFixture[str]) -> None:
    """Validate command can write deterministic snapshot metadata."""
    source_root = Path("build") / "test_cli_validate_snapshot" / "sources"
    source_dir = source_root / "Demo Genre"
    case_dir = Path("build") / "test_cli_validate_snapshot" / "cases"
    snapshot_dir = Path("build") / "test_cli_validate_snapshot" / "snapshot"
    shutil.rmtree(snapshot_dir, ignore_errors=True)
    source_dir.mkdir(parents=True, exist_ok=True)
    case_dir.mkdir(parents=True, exist_ok=True)
    for existing_case in case_dir.glob("*.json"):
        existing_case.unlink()
    (source_dir / "Demo Chapter 1.txt").write_text(
        "Chapter 1\nMark found a brass key.",
        encoding="utf-8",
    )
    (source_dir / "Demo Chapter 2.txt").write_text(
        "Chapter 2\nMark opened the archive.",
        encoding="utf-8",
    )
    (case_dir / "demo_validation_case.json").write_text(
        json.dumps(
            {
                "case_id": "demo_validation_case",
                "title": "Demo",
                "genre": "Demo",
                "source_directory": "Demo Genre",
                "chapter_glob": "*.txt",
                "expected_import": _cli_validation_expected_import(source_dir),
                "expected_extraction": _cli_validation_expected_extraction(source_dir),
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "validate",
            "--case-dir",
            str(case_dir),
            "--source-root",
            str(source_root),
            "--snapshot-dir",
            str(snapshot_dir),
            "--summary-only",
        ]
    )
    output = capsys.readouterr().out
    snapshot = json.loads(
        (snapshot_dir / "validation_result.json").read_text(encoding="utf-8")
    )
    readme = (snapshot_dir / "README.md").read_text(encoding="utf-8")

    assert exit_code == 0
    assert "Validation Summary" in output
    assert snapshot["passed"] is True
    assert snapshot["totals"]["cases"] == 1
    assert "Mark found a brass key." not in json.dumps(snapshot, ensure_ascii=False)
    assert "Mark opened the archive." not in json.dumps(snapshot, ensure_ascii=False)
    assert "does not store chapter text" in readme
    assert "Mark found a brass key." not in readme
    assert "Mark opened the archive." not in readme
    assert "Scene Text:" not in readme
    assert "Evidence Anchors:" not in readme


def test_validate_snapshot_json_matches_cli_json(capsys: CaptureFixture[str]) -> None:
    """Validation snapshot JSON should match validate --format json output."""
    source_root = Path("build") / "test_cli_validate_snapshot_json" / "sources"
    source_dir = source_root / "Demo Genre"
    case_dir = Path("build") / "test_cli_validate_snapshot_json" / "cases"
    snapshot_dir = Path("build") / "test_cli_validate_snapshot_json" / "snapshot"
    shutil.rmtree(snapshot_dir, ignore_errors=True)
    source_dir.mkdir(parents=True, exist_ok=True)
    case_dir.mkdir(parents=True, exist_ok=True)
    for existing_case in case_dir.glob("*.json"):
        existing_case.unlink()
    (source_dir / "Demo Chapter 1.txt").write_text(
        "Chapter 1\nMark found a brass key.",
        encoding="utf-8",
    )
    (source_dir / "Demo Chapter 2.txt").write_text(
        "Chapter 2\nMark opened the archive.",
        encoding="utf-8",
    )
    (case_dir / "demo_validation_case.json").write_text(
        json.dumps(
            {
                "case_id": "demo_validation_case",
                "title": "Demo",
                "genre": "Demo",
                "source_directory": "Demo Genre",
                "chapter_glob": "*.txt",
                "expected_import": _cli_validation_expected_import(source_dir),
                "expected_extraction": _cli_validation_expected_extraction(source_dir),
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "validate",
            "--case-dir",
            str(case_dir),
            "--source-root",
            str(source_root),
            "--format",
            "json",
            "--snapshot-dir",
            str(snapshot_dir),
        ]
    )
    output = capsys.readouterr().out
    snapshot_output = (snapshot_dir / "validation_result.json").read_text(
        encoding="utf-8"
    )

    assert exit_code == 0
    assert snapshot_output == output


def test_validate_snapshot_rejects_nonempty_directory(
    capsys: CaptureFixture[str],
) -> None:
    """Validate snapshots refuse to overwrite existing reference files."""
    source_root = Path("build") / "test_cli_validate_snapshot_reject" / "sources"
    source_dir = source_root / "Demo Genre"
    case_dir = Path("build") / "test_cli_validate_snapshot_reject" / "cases"
    snapshot_dir = Path("build") / "test_cli_validate_snapshot_reject" / "snapshot"
    shutil.rmtree(snapshot_dir, ignore_errors=True)
    source_dir.mkdir(parents=True, exist_ok=True)
    case_dir.mkdir(parents=True, exist_ok=True)
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    for existing_case in case_dir.glob("*.json"):
        existing_case.unlink()
    (source_dir / "Demo Chapter 1.txt").write_text(
        "Chapter 1\nMark found a brass key.",
        encoding="utf-8",
    )
    (source_dir / "Demo Chapter 2.txt").write_text(
        "Chapter 2\nMark opened the archive.",
        encoding="utf-8",
    )
    (snapshot_dir / "existing.txt").write_text("keep me", encoding="utf-8")
    (case_dir / "demo_validation_case.json").write_text(
        json.dumps(
            {
                "case_id": "demo_validation_case",
                "title": "Demo",
                "genre": "Demo",
                "source_directory": "Demo Genre",
                "chapter_glob": "*.txt",
                "expected_import": _cli_validation_expected_import(source_dir),
                "expected_extraction": _cli_validation_expected_extraction(source_dir),
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "validate",
            "--case-dir",
            str(case_dir),
            "--source-root",
            str(source_root),
            "--snapshot-dir",
            str(snapshot_dir),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Validation snapshot directory must be empty or absent" in captured.err
    assert (snapshot_dir / "existing.txt").read_text(encoding="utf-8") == "keep me"


def test_validate_snapshot_rejects_file_path(capsys: CaptureFixture[str]) -> None:
    """Validate snapshots require a directory path."""
    source_root = Path("build") / "test_cli_validate_snapshot_file" / "sources"
    source_dir = source_root / "Demo Genre"
    case_dir = Path("build") / "test_cli_validate_snapshot_file" / "cases"
    snapshot_path = Path("build") / "test_cli_validate_snapshot_file" / "snapshot.txt"
    source_dir.mkdir(parents=True, exist_ok=True)
    case_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    for existing_case in case_dir.glob("*.json"):
        existing_case.unlink()
    (source_dir / "Demo Chapter 1.txt").write_text(
        "Chapter 1\nMark found a brass key.",
        encoding="utf-8",
    )
    (source_dir / "Demo Chapter 2.txt").write_text(
        "Chapter 2\nMark opened the archive.",
        encoding="utf-8",
    )
    snapshot_path.write_text("not a directory", encoding="utf-8")
    (case_dir / "demo_validation_case.json").write_text(
        json.dumps(
            {
                "case_id": "demo_validation_case",
                "title": "Demo",
                "genre": "Demo",
                "source_directory": "Demo Genre",
                "chapter_glob": "*.txt",
                "expected_import": _cli_validation_expected_import(source_dir),
                "expected_extraction": _cli_validation_expected_extraction(source_dir),
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "validate",
            "--case-dir",
            str(case_dir),
            "--source-root",
            str(source_root),
            "--snapshot-dir",
            str(snapshot_path),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Validation snapshot path must be a directory" in captured.err
    assert snapshot_path.read_text(encoding="utf-8") == "not a directory"


def test_validate_command_can_filter_by_case_id(capsys: CaptureFixture[str]) -> None:
    """Validate command can run a selected validation case."""
    source_root = Path("build") / "test_cli_validate_filter" / "sources"
    source_dir = source_root / "Demo Genre"
    case_dir = Path("build") / "test_cli_validate_filter" / "cases"
    source_dir.mkdir(parents=True, exist_ok=True)
    case_dir.mkdir(parents=True, exist_ok=True)
    for existing_case in case_dir.glob("*.json"):
        existing_case.unlink()
    (source_dir / "Demo Chapter 1.txt").write_text(
        "Chapter 1\nMark found a brass key.",
        encoding="utf-8",
    )
    (source_dir / "Demo Chapter 2.txt").write_text(
        "Chapter 2\nMark opened the archive.",
        encoding="utf-8",
    )
    (case_dir / "demo_validation_case.json").write_text(
        json.dumps(
            {
                "case_id": "demo_validation_case",
                "title": "Demo",
                "genre": "Demo",
                "source_directory": "Demo Genre",
                "chapter_glob": "*.txt",
                "expected_import": _cli_validation_expected_import(source_dir),
                "expected_extraction": _cli_validation_expected_extraction(source_dir),
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "validate",
            "--case-dir",
            str(case_dir),
            "--source-root",
            str(source_root),
            "--case-id",
            "demo_validation_case",
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Demo - Demo" in output
    assert "cases=1 passed=1 failed=0" in output
    assert "extraction_inputs=2 extraction_anchors=2" in output


def test_validate_command_can_list_cases(capsys: CaptureFixture[str]) -> None:
    """Validate command can list cases without running imports."""
    case_dir = Path("build") / "test_cli_validate_list" / "cases"
    case_dir.mkdir(parents=True, exist_ok=True)
    for existing_case in case_dir.glob("*.json"):
        existing_case.unlink()
    source_dir = Path("build") / "test_cli_validate_list" / "sources" / "Demo Genre"
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "Demo Chapter 1.txt").write_text(
        "Chapter 1\nMark found a brass key.",
        encoding="utf-8",
    )
    (source_dir / "Demo Chapter 2.txt").write_text(
        "Chapter 2\nMark opened the archive.",
        encoding="utf-8",
    )
    (case_dir / "demo_validation_case.json").write_text(
        json.dumps(
            {
                "case_id": "demo_validation_case",
                "title": "Demo",
                "genre": "Demo",
                "source_directory": "Demo Genre",
                "chapter_glob": "*.txt",
                "expected_import": _cli_validation_expected_import(source_dir),
                "expected_extraction": _cli_validation_expected_extraction(source_dir),
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "validate",
            "--case-dir",
            str(case_dir),
            "--source-root",
            "build/test_cli_validate_list/missing_sources",
            "--list-cases",
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Validation Cases" in output
    assert "demo_validation_case" in output
    assert "PASS" not in output


def test_validate_command_can_list_cases_as_json(capsys: CaptureFixture[str]) -> None:
    """Validate list-cases command can print machine-readable case metadata."""
    case_dir = Path("build") / "test_cli_validate_list_json" / "cases"
    case_dir.mkdir(parents=True, exist_ok=True)
    for existing_case in case_dir.glob("*.json"):
        existing_case.unlink()
    source_dir = Path("build") / "test_cli_validate_list_json" / "sources" / "Demo Genre"
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "Demo Chapter 1.txt").write_text(
        "Chapter 1\nMark found a brass key.",
        encoding="utf-8",
    )
    (source_dir / "Demo Chapter 2.txt").write_text(
        "Chapter 2\nMark opened the archive.",
        encoding="utf-8",
    )
    (case_dir / "demo_validation_case.json").write_text(
        json.dumps(
            {
                "case_id": "demo_validation_case",
                "title": "Demo",
                "genre": "Demo",
                "source_directory": "Demo Genre",
                "chapter_glob": "*.txt",
                "expected_import": _cli_validation_expected_import(source_dir),
                "expected_extraction": _cli_validation_expected_extraction(source_dir),
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "validate",
            "--case-dir",
            str(case_dir),
            "--source-root",
            "build/test_cli_validate_list_json/missing_sources",
            "--list-cases",
            "--format",
            "json",
        ]
    )
    output = capsys.readouterr().out
    exported = json.loads(output)

    assert exit_code == 0
    assert exported["cases"][0]["case_id"] == "demo_validation_case"
    assert exported["cases"][0]["genre"] == "Demo"


def test_validate_list_cases_rejects_snapshot_dir(capsys: CaptureFixture[str]) -> None:
    """Validate list-cases cannot silently ignore snapshot requests."""
    case_dir = Path("build") / "test_cli_validate_list_snapshot" / "cases"
    case_dir.mkdir(parents=True, exist_ok=True)
    for existing_case in case_dir.glob("*.json"):
        existing_case.unlink()

    exit_code = main(
        [
            "validate",
            "--case-dir",
            str(case_dir),
            "--list-cases",
            "--snapshot-dir",
            "build/test_cli_validate_list_snapshot/snapshot",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "snapshots cannot be written when listing cases" in captured.err


def test_validate_json_command_fails_nonzero_on_validation_failure(
    capsys: CaptureFixture[str],
) -> None:
    """Validate JSON command reports failures with a nonzero exit code."""
    source_root = Path("build") / "test_cli_validate_json_failure" / "sources"
    source_dir = source_root / "Demo Genre"
    case_dir = Path("build") / "test_cli_validate_json_failure" / "cases"
    source_dir.mkdir(parents=True, exist_ok=True)
    case_dir.mkdir(parents=True, exist_ok=True)
    for existing_case in case_dir.glob("*.json"):
        existing_case.unlink()
    (source_dir / "Demo Chapter 1.txt").write_text(
        "Chapter 1\nMark found a brass key.",
        encoding="utf-8",
    )
    (source_dir / "Demo Chapter 2.txt").write_text(
        "Chapter 2\nMark opened the archive.",
        encoding="utf-8",
    )
    expected_import = _cli_validation_expected_import(source_dir)
    expected_import["evidence_anchors"] = 999
    (case_dir / "demo_validation_case.json").write_text(
        json.dumps(
            {
                "case_id": "demo_validation_case",
                "title": "Demo",
                "genre": "Demo",
                "source_directory": "Demo Genre",
                "chapter_glob": "*.txt",
                "expected_import": expected_import,
                "expected_extraction": _cli_validation_expected_extraction(source_dir),
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "validate",
            "--case-dir",
            str(case_dir),
            "--source-root",
            str(source_root),
            "--format",
            "json",
        ]
    )
    captured = capsys.readouterr()
    exported = json.loads(captured.out)

    assert exit_code == 1
    assert exported["passed"] is False
    assert exported["score"] == 0
    assert "Validation suite failed." in captured.err
    assert exported["results"][0]["errors"] == [
        "import.evidence_anchors: expected 999, got 2"
    ]


def test_validate_text_command_fails_nonzero_on_validation_failure(
    capsys: CaptureFixture[str],
) -> None:
    """Validate text command reports case errors with a nonzero exit code."""
    source_root = Path("build") / "test_cli_validate_text_failure" / "sources"
    source_dir = source_root / "Demo Genre"
    case_dir = Path("build") / "test_cli_validate_text_failure" / "cases"
    source_dir.mkdir(parents=True, exist_ok=True)
    case_dir.mkdir(parents=True, exist_ok=True)
    for existing_case in case_dir.glob("*.json"):
        existing_case.unlink()
    (source_dir / "Demo Chapter 1.txt").write_text(
        "Chapter 1\nMark found a brass key.",
        encoding="utf-8",
    )
    (source_dir / "Demo Chapter 2.txt").write_text(
        "Chapter 2\nMark opened the archive.",
        encoding="utf-8",
    )
    expected_import = _cli_validation_expected_import(source_dir)
    expected_import["evidence_anchors"] = 999
    (case_dir / "demo_validation_case.json").write_text(
        json.dumps(
            {
                "case_id": "demo_validation_case",
                "title": "Demo",
                "genre": "Demo",
                "source_directory": "Demo Genre",
                "chapter_glob": "*.txt",
                "expected_import": expected_import,
                "expected_extraction": _cli_validation_expected_extraction(source_dir),
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "validate",
            "--case-dir",
            str(case_dir),
            "--source-root",
            str(source_root),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Demo - Demo" in captured.out
    assert "FAIL" in captured.out
    assert "import.evidence_anchors: expected 999, got 2" in captured.out
    assert "cases=1 passed=0 failed=1" in captured.out
    assert "Validation suite failed." in captured.err


def _cli_validation_expected_import(source_dir: Path) -> dict[str, int | str]:
    """Return expected import metrics for the CLI validation fixture."""
    chapter_files = tuple(sorted(source_dir.glob("*.txt")))
    imported = StoryImporter().import_text(
        source_id="demo_validation_case",
        title="Demo",
        text="\n\n".join(
            (
                "Chapter 1\nMark found a brass key.",
                "Chapter 2\nMark opened the archive.",
            )
        ),
    )
    return {
        "chapter_files": 2,
        "source_manifest_digest": _source_manifest_digest(chapter_files),
        "chapters": len(imported.story.chapters),
        "scenes": sum(len(chapter.scenes) for chapter in imported.story.chapters),
        "paragraphs": len(imported.paragraphs),
        "sentences": sum(len(paragraph.sentences) for paragraph in imported.paragraphs),
        "evidence_anchors": len(imported.anchors),
        "import_digest": _structure_digest(imported),
    }


def _cli_validation_expected_extraction(source_dir: Path) -> dict[str, int | str]:
    """Return expected extraction-readiness metrics for the CLI validation fixture."""
    imported = StoryImporter().import_text(
        source_id="demo_validation_case",
        title="Demo",
        text="\n\n".join(
            (
                "Chapter 1\nMark found a brass key.",
                "Chapter 2\nMark opened the archive.",
            )
        ),
    )
    return {
        "scene_inputs": sum(len(chapter.scenes) for chapter in imported.story.chapters),
        "evidence_anchors": len(imported.anchors),
        "extraction_input_digest": _extraction_input_digest(imported),
        "extraction_prompt_digest": _extraction_prompt_digest(imported),
    }


def weapon_payload(anchor_id: str, weapon: str) -> dict[str, object]:
    """Build a multi-scene AI payload for a weapon fact."""
    normalized_weapon = weapon.lower().replace(" ", "_")
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
                "fact_id": f"fact_character_mark_current_weapon_{normalized_weapon}",
                "entity_id": "character_mark",
                "attribute": "current_weapon",
                "value": weapon,
                "evidence_anchor_id": anchor_id,
                "confidence": 0.95,
            }
        ],
        "relationships": [],
        "state_changes": [],
    }
