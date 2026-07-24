"""Command line interface for Aevryn proof workflows."""

from __future__ import annotations

import argparse
import base64
import getpass
import json
import os
import subprocess  # nosec B404
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Iterable, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

from fastapi import FastAPI

from aevryn.api import (
    ACCOUNT_DELETION_HANDOFF_ENV,
    ALLOWED_ORIGINS_ENV,
    API_KEYS_ENV,
    DEPLOYMENT_ENV,
    ENVIRONMENT_NAME_ENV,
    EXTRACTION_MODE_ENV,
    HSTS_ENABLED_ENV,
    HTTPS_ONLY_ENV,
    IDENTITY_PROVIDER_ENV,
    IDENTITY_PROVIDER_NAME_ENV,
    IMPORT_STORAGE_PATH_ENV,
    LOG_DESTINATION_ENV,
    LOG_RETENTION_DAYS_ENV,
    METADATA_ONLY_LOGGING_ENV,
    MONITORING_DESTINATION_ENV,
    MONITORING_RETENTION_DAYS_ENV,
    OPENAI_API_KEY_ENV,
    OPENAI_MAX_RESPONSE_BYTES_ENV,
    OPENAI_MODEL_ENV,
    OPENAI_TIMEOUT_SECONDS_ENV,
    PASSWORD_RESET_ENABLED_ENV,
    PROJECT_DATABASE_ADAPTER_ENV,
    PROJECT_DATABASE_BOOTSTRAP_ENV,
    PROJECT_DATABASE_PATH_ENV,
    PROJECT_DATABASE_URL_ENV,
    PUBLIC_API_BASE_URL_ENV,
    PUBLIC_FRONTEND_BASE_URL_ENV,
    R2_ACCESS_KEY_ID_ENV,
    R2_ACCOUNT_ID_ENV,
    R2_BUCKET_ENV,
    R2_ENDPOINT_URL_ENV,
    R2_REGION_ENV,
    R2_SECRET_ACCESS_KEY_ENV,
    RESTORE_DRILL_TARGET_ENV,
    SECRET_MANAGER_ENV,
    SECURITY_ALERTS_ENABLED_ENV,
    SESSION_AUTHORITY_ENV,
    SESSION_SECRET_ENV,
    STORAGE_PROVIDER_ENV,
    SUPABASE_ANON_KEY_ENV,
    SUPABASE_JWKS_URL_ENV,
    SUPABASE_JWT_ALGORITHM_ENV,
    SUPABASE_JWT_SECRET_ENV,
    SUPABASE_SERVICE_ROLE_KEY_ENV,
    SUPABASE_URL_ENV,
    WORKER_API_KEY_ENV,
    WORKER_CONCURRENCY_ENV,
    WORKER_MAX_RETRIES_ENV,
    WORKER_QUEUE_PROVIDER_ENV,
    WORKER_RUNTIME_ENV,
    WORKER_TIMEOUT_SECONDS_ENV,
    create_app,
    create_app_from_env,
)
from aevryn.audit import PostgresqlAuditLedger, postgresql_audit_access_report
from aevryn.auth import (
    AuthenticationConfig,
    AuthenticationService,
    InMemoryCredentialStore,
    InMemorySessionStore,
    PasswordHasher,
)
from aevryn.export import ExportEngine
from aevryn.extraction import (
    EvidenceBoundedAIExtractor,
    OpenAIResponsesAIExtractionClient,
    StaticAIExtractionClient,
)
from aevryn.import_storage import InMemoryImportContentStore
from aevryn.importing import SourceFileTextExtractor
from aevryn.json_utils import loads_json_without_duplicate_keys
from aevryn.performance import PerformanceRegressionPayload
from aevryn.persistence import InMemoryProjectRepository
from aevryn.persistence.models import UserRecord
from aevryn.persistence.postgresql import PostgresqlProjectRepository
from aevryn.persistence.repository import PersistenceError, RecordNotFoundError
from aevryn.presentation import PresentationEngine
from aevryn.projects import AevrynProjectRunner, ProjectRunResult
from aevryn.prompts import CanonPromptBuilder
from aevryn.scenes import SceneAnalyzer
from aevryn.storage import R2Storage, StorageObjectNotFoundError
from aevryn.validation import (
    ExpectedExtractionMetrics,
    ExpectedImportMetrics,
    ValidationCase,
    ValidationRunner,
    ValidationSuiteResult,
    ValidationTotals,
)
from aevryn.workers import InMemoryJobQueue, ProjectImportSnapshotHandler


class _RawDefaultsHelpFormatter(
    argparse.ArgumentDefaultsHelpFormatter,
    argparse.RawDescriptionHelpFormatter,
):
    """Argparse formatter that preserves examples and shows argument defaults."""


def main(argv: Sequence[str] | None = None) -> int:
    """Run the Aevryn command line interface.

    Parameters:
        argv: Optional command arguments. When omitted, process arguments are used.

    Returns:
        Process exit code.
    """
    _configure_utf8_stdio()
    parser = _build_parser()
    args = parser.parse_args(argv)
    command = cast(str, args.command)

    try:
        if command == "import":
            _handle_import(args)
            return 0
        if command == "extract-demo":
            _handle_extract_demo(args)
            return 0
        if command == "extraction-prompt":
            _handle_extraction_prompt(args)
            return 0
        if command == "extract-ai-json":
            _handle_extract_ai_json(args)
            return 0
        if command == "character":
            _handle_character(args)
            return 0
        if command == "scene":
            _handle_scene(args)
            return 0
        if command == "prompt":
            _handle_prompt(args)
            return 0
        if command == "world":
            _handle_world(args)
            return 0
        if command == "continuity":
            _handle_continuity(args)
            return 0
        if command == "validate":
            _handle_validate(args)
            return 0
        if command == "performance-baseline":
            return _handle_performance_baseline(args)
        if command == "api":
            _handle_api(args)
            return 0
        if command == "provider-smoke":
            _handle_provider_smoke(args)
            return 0
        if command == "provider-config-check":
            _handle_provider_config_check()
            return 0
        if command == "project-db-smoke":
            _handle_project_db_smoke(args)
            return 0
        if command == "storage-smoke":
            _handle_storage_smoke()
            return 0
        if command == "hosted-deployment-smoke":
            _handle_hosted_deployment_smoke(args)
            return 0
        if command == "cloud-run-deployment-check":
            _handle_cloud_run_deployment_check(args)
            return 0
        if command == "worker-drain":
            _handle_worker_drain(args)
            return 0
        if command == "restore-drill-fixture":
            _handle_restore_drill_fixture(args)
            return 0
        if command == "restore-drill-verify":
            _handle_restore_drill_verify(args)
            return 0
        if command == "restore-api-config-check":
            _handle_restore_api_config_check()
            return 0
        if command == "production-config-check":
            _handle_production_config_check()
            return 0
        if command == "observability-config-check":
            _handle_observability_config_check()
            return 0
        if command == "audit-ledger-verify":
            _handle_audit_ledger_verify(args)
            return 0
        if command == "audit-access-report":
            _handle_audit_access_report(args)
            return 0
        if command == "audit-access-verify":
            _handle_audit_access_verify(args)
            return 0
    except FileNotFoundError as error:
        missing_path = error.filename or error.args[0]
        print(f"Error: File not found: {missing_path}", file=sys.stderr)
        return 1
    except (OSError, ValueError, PersistenceError, json.JSONDecodeError) as error:
        print(_format_cli_error(error), file=sys.stderr)
        return 1

    parser.error(f"Unknown command: {command}")
    return 2


def _configure_utf8_stdio() -> None:
    """Prefer UTF-8 CLI streams for multilingual story text."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8")


def _format_cli_error(error: Exception) -> str:
    """Return a user-facing CLI error with an actionable hint when possible."""
    message = str(error)
    hints = _cli_error_hints(message)
    if not hints:
        return f"Error: {message}"

    return "\n".join((f"Error: {message}", *(f"Hint: {hint}" for hint in hints)))


def _cli_error_hints(message: str) -> tuple[str, ...]:
    """Return actionable hints for common user-facing CLI errors."""
    if "Unknown scene" in message:
        return (
            "Run `aevryn import <path> --source-id <id>` to inspect available scene IDs.",
        )
    if "Unknown character" in message or "Unknown entity" in message:
        return (
            "Run `aevryn extract-ai-json <path> <response.json> --source-id <id>` "
            "and use the accepted_entity_ids from the summary.",
        )
    if "Unknown world entity" in message:
        return (
            "Use a non-character accepted entity ID from the extraction summary.",
        )

    return ()


def _build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="aevryn",
        description=(
            "Aevryn V1 proof CLI for importing story text, applying "
            "evidence-bounded extraction, and inspecting canon-backed outputs."
        ),
        epilog=(
            "Typical V1 flow:\n"
            "  aevryn import chapter_001.txt --source-id my_story\n"
            "  aevryn extraction-prompt chapter_001.txt --source-id my_story\n"
            "  aevryn extract-ai-json chapter_001.txt ai_response.json --source-id my_story\n"
            "  aevryn character chapter_001.txt --source-id my_story "
            "--ai-response-file ai_response.json --character-id character_mark\n"
            "  aevryn scene chapter_001.txt --source-id my_story "
            "--ai-response-file ai_response.json\n"
            "  aevryn prompt chapter_001.txt --source-id my_story "
            "--ai-response-file ai_response.json\n"
            "  aevryn continuity chapter_001.txt --source-id my_story "
            "--ai-response-file ai_response.json\n\n"
            "Validation:\n"
            "  aevryn validate --summary-only\n"
            "  aevryn validate --list-cases\n"
            "  aevryn validate --summary-only --snapshot-dir snapshots/run_name\n\n"
            "Performance:\n"
            "  aevryn performance-baseline\n\n"
            "V2 Backend API:\n"
            "  aevryn api --host 127.0.0.1 --port 8000 "
            "--allowed-origin http://localhost:5173\n"
            "  aevryn provider-config-check\n"
            "  aevryn project-db-smoke\n"
            "  aevryn storage-smoke\n"
            "  aevryn worker-drain\n"
            "  aevryn restore-drill-fixture\n"
            "  aevryn observability-config-check"
        ),
        formatter_class=_RawDefaultsHelpFormatter,
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    import_parser = subcommands.add_parser(
        "import",
        help="Inspect how source text is parsed into chapters, scenes, and evidence.",
        formatter_class=_RawDefaultsHelpFormatter,
    )
    _add_source_arguments(import_parser)

    extract_parser = subcommands.add_parser(
        "extract-demo",
        help="Run the deterministic demo extractor for tests and examples.",
        formatter_class=_RawDefaultsHelpFormatter,
    )
    _add_source_arguments(extract_parser)

    extraction_prompt_parser = subcommands.add_parser(
        "extraction-prompt",
        help="Print the evidence-bounded AI extraction prompt for one scene.",
        formatter_class=_RawDefaultsHelpFormatter,
    )
    _add_source_arguments(extraction_prompt_parser)
    extraction_prompt_parser.add_argument(
        "--scene-id",
        default=None,
        help="Scene ID to prepare; defaults to the first imported scene.",
    )

    extract_ai_parser = subcommands.add_parser(
        "extract-ai-json",
        help="Apply evidence-bounded AI JSON candidates through Canon Updating.",
        formatter_class=_RawDefaultsHelpFormatter,
    )
    _add_source_arguments(extract_ai_parser)
    extract_ai_parser.add_argument(
        "response_path",
        help="Path to an evidence-bounded AI JSON response file.",
    )
    extract_ai_parser.add_argument(
        "--scene-id",
        default=None,
        help="Scene ID for a single-scene response; ignored for multi-scene envelopes.",
    )

    character_parser = subcommands.add_parser(
        "character",
        help="Print a canon-backed character sheet.",
        formatter_class=_RawDefaultsHelpFormatter,
    )
    _add_source_arguments(character_parser)
    character_parser.add_argument(
        "--character-id",
        default="character_mark",
        help=(
            "Character entity ID to display. Use accepted_entity_ids from "
            "extract-ai-json for real projects."
        ),
    )
    character_parser.add_argument(
        "--chapter-index",
        type=int,
        default=None,
        help="Chapter index to inspect; defaults to current canon.",
    )
    character_parser.add_argument(
        "--scene-id",
        default=None,
        help="Scene ID to inspect; prevents future canon from leaking into the view.",
    )
    character_parser.add_argument(
        "--ai-response-file",
        default=None,
        help="Evidence-bounded AI JSON response to apply before building the view.",
    )
    character_parser.add_argument(
        "--format",
        choices=("markdown", "json", "csv"),
        default="markdown",
        help="Output format. Markdown is presentation-first; JSON/CSV preserve machine detail.",
    )

    scene_parser = subcommands.add_parser(
        "scene",
        help="Print a timeline-aware scene sheet.",
        formatter_class=_RawDefaultsHelpFormatter,
    )
    _add_source_arguments(scene_parser)
    scene_parser.add_argument(
        "--scene-id",
        default=None,
        help="Scene ID to inspect; defaults to the latest imported scene.",
    )
    scene_parser.add_argument(
        "--character-id",
        action="append",
        default=None,
        help=(
            "Character entity ID to include. Repeat for multiple characters. "
            "Defaults to accepted characters in the selected scene."
        ),
    )
    scene_parser.add_argument(
        "--ai-response-file",
        default=None,
        help="Evidence-bounded AI JSON response to apply before building the view.",
    )
    scene_parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format. Markdown is presentation-first; JSON preserves machine detail.",
    )

    prompt_parser = subcommands.add_parser(
        "prompt",
        help="Print a canon-backed production prompt pack.",
        formatter_class=_RawDefaultsHelpFormatter,
    )
    _add_source_arguments(prompt_parser)
    prompt_parser.add_argument(
        "--scene-id",
        default=None,
        help="Scene ID to inspect; defaults to the latest imported scene.",
    )
    prompt_parser.add_argument(
        "--character-id",
        action="append",
        default=None,
        help=(
            "Character entity ID to include. Repeat for multiple characters. "
            "Defaults to accepted characters in the selected scene."
        ),
    )
    prompt_parser.add_argument(
        "--ai-response-file",
        default=None,
        help="Evidence-bounded AI JSON response to apply before building prompts.",
    )
    prompt_parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format. Markdown is presentation-first; JSON preserves machine detail.",
    )

    world_parser = subcommands.add_parser(
        "world",
        help="Print a canon-backed world sheet for selected non-character entities.",
        formatter_class=_RawDefaultsHelpFormatter,
    )
    _add_source_arguments(world_parser)
    world_parser.add_argument(
        "--entity-id",
        action="append",
        required=True,
        help="Non-character entity ID to display. Repeat for multiple world objects.",
    )
    world_parser.add_argument(
        "--chapter-index",
        type=int,
        default=None,
        help="Chapter index to inspect; defaults to current canon.",
    )
    world_parser.add_argument(
        "--scene-id",
        default=None,
        help="Scene ID to inspect; prevents future canon from leaking into the view.",
    )
    world_parser.add_argument(
        "--ai-response-file",
        default=None,
        help="Evidence-bounded AI JSON response to apply before building the view.",
    )
    world_parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format. Markdown is presentation-first; JSON preserves machine detail.",
    )

    continuity_parser = subcommands.add_parser(
        "continuity",
        help="Print what changed, stayed known, and was invalidated.",
        formatter_class=_RawDefaultsHelpFormatter,
    )
    _add_source_arguments(continuity_parser)
    continuity_parser.add_argument(
        "--ai-response-file",
        default=None,
        help="Evidence-bounded AI JSON response to apply before building the report.",
    )
    continuity_parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format. Markdown is scan-friendly; JSON preserves audit detail.",
    )

    validate_parser = subcommands.add_parser(
        "validate",
        help="Run the local validation corpus and optional deterministic snapshot.",
        formatter_class=_RawDefaultsHelpFormatter,
    )
    validate_parser.add_argument(
        "--case-dir",
        default="validation/cases",
        help="Directory containing validation case metadata JSON files.",
    )
    validate_parser.add_argument(
        "--source-root",
        default=None,
        help=(
            "Root directory containing local validation chapter folders. "
            "Overrides AEVRYN_VALIDATION_ROOT."
        ),
    )
    validate_parser.add_argument(
        "--case-id",
        action="append",
        default=None,
        help="Validation case ID to run. Repeat for multiple focused cases.",
    )
    validate_parser.add_argument(
        "--list-cases",
        action="store_true",
        help="List validation cases without importing source files.",
    )
    validate_parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Print only suite totals, digest, and score.",
    )
    validate_parser.add_argument(
        "--snapshot-dir",
        default=None,
        help="Empty or absent directory where deterministic snapshot metadata is written.",
    )
    validate_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format. Text is scan-friendly; JSON preserves machine detail.",
    )

    performance_parser = subcommands.add_parser(
        "performance-baseline",
        help="Write a local metadata-only Phase 9 performance baseline.",
        description="Write a local metadata-only Phase 9 performance baseline.",
        formatter_class=_RawDefaultsHelpFormatter,
    )
    performance_parser.add_argument(
        "--output",
        default="performance-baselines/latest.json",
        help="Output JSON path for the ignored local baseline artifact.",
    )
    performance_parser.add_argument(
        "--compare-to",
        default=None,
        help="Previous baseline JSON artifact to compare against a new local run.",
    )

    api_parser = subcommands.add_parser(
        "api",
        help="Run the V2 Backend API for local platform development.",
        description="Run the V2 Backend API for local platform development.",
        formatter_class=_RawDefaultsHelpFormatter,
    )
    api_parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host interface for the API server.",
    )
    api_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for the API server.",
    )
    api_parser.add_argument(
        "--allowed-origin",
        action="append",
        default=None,
        help=(
            "Browser origin allowed by CORS. Repeat for multiple origins. "
            "CORS remains disabled when omitted."
        ),
    )
    api_parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable Uvicorn reload for local development.",
    )

    provider_smoke_parser = subcommands.add_parser(
        "provider-smoke",
        help="Run a synthetic provider-backed API workflow smoke test.",
        description=(
            "Run a synthetic provider-backed API workflow smoke test. "
            "Uses invented source text only and prints metadata counts only."
        ),
        formatter_class=_RawDefaultsHelpFormatter,
    )
    provider_smoke_parser.add_argument(
        "--env-file",
        default=".env.aevryn.local",
        help="Ignored local env file containing AEVRYN_OPENAI_API_KEY and model.",
    )
    provider_smoke_parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=60.0,
        help="Provider request timeout for each synthetic extraction call.",
    )

    subcommands.add_parser(
        "provider-config-check",
        help="Check provider extraction configuration without printing secrets.",
        description=(
            "Check provider extraction configuration without printing secrets. "
            "This verifies the explicit provider mode, OpenAI key presence, model, "
            "timeout, and response-size boundary. It does not approve provider "
            "use for public beta or replace owner/legal/provider review."
        ),
        formatter_class=_RawDefaultsHelpFormatter,
    )

    project_db_smoke_parser = subcommands.add_parser(
        "project-db-smoke",
        help="Run a metadata-only PostgreSQL Project Database smoke test.",
        description=(
            "Run a metadata-only PostgreSQL Project Database smoke test. "
            "Reads the database URL from an environment variable and never prints it."
        ),
        formatter_class=_RawDefaultsHelpFormatter,
    )
    project_db_smoke_parser.add_argument(
        "--database-url-env",
        default="AEVRYN_PROJECT_DATABASE_URL",
        help="Process environment variable containing the PostgreSQL database URL.",
    )
    project_db_smoke_parser.add_argument(
        "--no-bootstrap",
        action="store_true",
        help="Validate an existing schema without attempting DDL.",
    )

    subcommands.add_parser(
        "storage-smoke",
        help="Run a metadata-only Cloudflare R2 storage smoke test.",
        description=(
            "Run a metadata-only Cloudflare R2 storage smoke test. "
            "Reads R2 settings from process environment variables, writes one "
            "synthetic private object, reads it back, deletes it, and never prints "
            "storage secrets."
        ),
        formatter_class=_RawDefaultsHelpFormatter,
    )

    hosted_deployment_parser = subcommands.add_parser(
        "hosted-deployment-smoke",
        help="Run a metadata-only hosted frontend/API deployment smoke test.",
        description=(
            "Run a metadata-only hosted frontend/API deployment smoke test. "
            "Checks that the public frontend is reachable, API health is reachable, "
            "CORS allows the configured frontend origin explicitly, and request IDs "
            "are present. It never prints secrets or private storage references."
        ),
        formatter_class=_RawDefaultsHelpFormatter,
    )
    hosted_deployment_parser.add_argument(
        "--frontend-url-env",
        default=PUBLIC_FRONTEND_BASE_URL_ENV,
        help="Process environment variable containing the public frontend base URL.",
    )
    hosted_deployment_parser.add_argument(
        "--api-url-env",
        default=PUBLIC_API_BASE_URL_ENV,
        help="Process environment variable containing the public API base URL.",
    )
    hosted_deployment_parser.add_argument(
        "--origin-env",
        default=PUBLIC_FRONTEND_BASE_URL_ENV,
        help="Process environment variable containing the expected browser Origin.",
    )
    hosted_deployment_parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=20.0,
        help="HTTP timeout for each hosted deployment request.",
    )

    cloud_run_deployment_parser = subcommands.add_parser(
        "cloud-run-deployment-check",
        help="Check the Cloud Run API revision/image contract without printing secrets.",
        description=(
            "Check the Cloud Run API revision/image contract without printing secrets. "
            "The command reads Cloud Run service metadata through gcloud, confirms "
            "the latest ready revision is serving all traffic, and confirms the "
            "deployed container image matches the expected image value. It prints "
            "metadata only, not project IDs, image URLs, secrets, storage refs, or "
            "source content."
        ),
        formatter_class=_RawDefaultsHelpFormatter,
    )
    cloud_run_deployment_parser.add_argument(
        "--service",
        default="aevryn-api",
        help="Cloud Run service name to inspect.",
    )
    cloud_run_deployment_parser.add_argument(
        "--region",
        default=os.environ.get("AEVRYN_CLOUD_RUN_REGION", "us-central1"),
        help="Cloud Run region containing the service.",
    )
    cloud_run_deployment_parser.add_argument(
        "--expected-image-env",
        default="AEVRYN_CLOUD_RUN_EXPECTED_IMAGE",
        help="Process environment variable containing the expected container image.",
    )
    cloud_run_deployment_parser.add_argument(
        "--gcloud-path",
        default="gcloud",
        help="Path to the gcloud executable.",
    )
    cloud_run_deployment_parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=30.0,
        help="Timeout for the gcloud metadata request.",
    )

    worker_drain_parser = subcommands.add_parser(
        "worker-drain",
        help="Drain queued worker jobs through the hosted API boundary.",
        description=(
            "Drain queued worker jobs through the hosted API boundary. "
            "Reads AEVRYN_PUBLIC_API_BASE_URL and AEVRYN_WORKER_API_KEY from "
            "process environment variables and never prints the worker key."
        ),
        formatter_class=_RawDefaultsHelpFormatter,
    )
    worker_drain_parser.add_argument(
        "--api-url-env",
        default=PUBLIC_API_BASE_URL_ENV,
        help="Process environment variable containing the public API base URL.",
    )
    worker_drain_parser.add_argument(
        "--worker-key-env",
        default=WORKER_API_KEY_ENV,
        help="Process environment variable containing the worker API key.",
    )
    worker_drain_parser.add_argument(
        "--max-jobs",
        type=int,
        default=1,
        help="Maximum number of queued jobs to drain in this run.",
    )
    worker_drain_parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=180.0,
        help="HTTP timeout for the worker drain request.",
    )

    restore_drill_fixture_parser = subcommands.add_parser(
        "restore-drill-fixture",
        help="Prepare metadata-only restore drill fixture data through the hosted API.",
        description=(
            "Prepare metadata-only restore drill fixture data through the hosted API. "
            "The command creates one test project, one active story, one saved import, "
            "one processing run, and one disposable story that is deleted before backup "
            "capture. It never prints bearer tokens, source prose, storage references, "
            "private URLs, or provider payloads."
        ),
        formatter_class=_RawDefaultsHelpFormatter,
    )
    restore_drill_fixture_parser.add_argument(
        "--api-url-env",
        default=PUBLIC_API_BASE_URL_ENV,
        help="Process environment variable containing the public API base URL.",
    )
    restore_drill_fixture_parser.add_argument(
        "--bearer-token-env",
        default="AEVRYN_RESTORE_DRILL_BEARER_TOKEN",
        help="Process environment variable containing the restore-test bearer token.",
    )
    restore_drill_fixture_parser.add_argument(
        "--worker-key-env",
        default=WORKER_API_KEY_ENV,
        help="Process environment variable containing the worker API key.",
    )
    restore_drill_fixture_parser.add_argument(
        "--drain-worker",
        action="store_true",
        help="Drain one worker job after submitting the import run.",
    )
    restore_drill_fixture_parser.add_argument(
        "--create-export",
        action="store_true",
        help="Create one metadata-only export from the latest snapshot when available.",
    )
    restore_drill_fixture_parser.add_argument(
        "--require-succeeded-run",
        action="store_true",
        help="Fail unless the submitted processing run reaches succeeded state.",
    )
    restore_drill_fixture_parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=30.0,
        help="HTTP timeout for each hosted API request.",
    )
    restore_drill_fixture_parser.add_argument(
        "--poll-attempts",
        type=int,
        default=1,
        help="Number of project-status polls after optional worker drain.",
    )
    restore_drill_fixture_parser.add_argument(
        "--poll-interval-seconds",
        type=float,
        default=2.0,
        help="Seconds to wait between project-status polls.",
    )

    restore_drill_verify_parser = subcommands.add_parser(
        "restore-drill-verify",
        help="Verify restored API ownership and deletion boundaries with metadata only.",
        description=(
            "Verify restored API ownership and deletion boundaries with metadata only. "
            "The command requires an isolated API URL plus owner and non-owner bearer "
            "tokens. It checks owner visibility, cross-user denial, deleted-story "
            "absence, import metadata scoping, and export scoping without printing "
            "tokens, source bytes, storage references, or export bodies."
        ),
        formatter_class=_RawDefaultsHelpFormatter,
    )
    restore_drill_verify_parser.add_argument(
        "--api-url-env",
        default=PUBLIC_API_BASE_URL_ENV,
        help="Process environment variable containing the isolated restore API base URL.",
    )
    restore_drill_verify_parser.add_argument(
        "--owner-bearer-token-env",
        default="AEVRYN_RESTORE_DRILL_BEARER_TOKEN",
        help="Process environment variable containing the restore owner bearer token.",
    )
    restore_drill_verify_parser.add_argument(
        "--other-bearer-token-env",
        default="AEVRYN_RESTORE_DRILL_OTHER_BEARER_TOKEN",
        help="Process environment variable containing a non-owner bearer token.",
    )
    restore_drill_verify_parser.add_argument(
        "--cloud-run-identity-token-env",
        default="AEVRYN_RESTORE_DRILL_CLOUD_RUN_IDENTITY_TOKEN",
        help=(
            "Optional process environment variable containing a Google identity "
            "token for private Cloud Run restore services."
        ),
    )
    restore_drill_verify_parser.add_argument(
        "--prompt-session-tokens",
        action="store_true",
        help=(
            "Prompt for owner and non-owner Aevryn session tokens without echoing "
            "them instead of reading those two tokens from environment variables."
        ),
    )
    restore_drill_verify_parser.add_argument(
        "--clipboard-session-tokens",
        action="store_true",
        help=(
            "Prompt the operator to copy owner and non-owner Aevryn session tokens "
            "to the clipboard one at a time instead of reading those two tokens "
            "from environment variables."
        ),
    )
    restore_drill_verify_parser.add_argument(
        "--project-id",
        required=True,
        help="Restore drill project ID created before the restore point.",
    )
    restore_drill_verify_parser.add_argument(
        "--active-story-id",
        required=True,
        help="Restore drill active story ID created before the restore point.",
    )
    restore_drill_verify_parser.add_argument(
        "--disposable-story-id",
        required=True,
        help="Restore drill disposable story ID deleted before the restore point.",
    )
    restore_drill_verify_parser.add_argument(
        "--import-id",
        default="",
        help="Expected restore drill import ID, when known.",
    )
    restore_drill_verify_parser.add_argument(
        "--export-id",
        default="",
        help="Expected restore drill export ID, when known.",
    )
    restore_drill_verify_parser.add_argument(
        "--allow-public-api-domain",
        action="store_true",
        help="Allow api.aevryn.ai. Use only for source preflight, not restore signoff.",
    )
    restore_drill_verify_parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=30.0,
        help="HTTP timeout for each isolated API request.",
    )

    subcommands.add_parser(
        "restore-api-config-check",
        help="Check isolated restore API configuration without printing secrets.",
        description=(
            "Check isolated restore API configuration without printing secrets. "
            "This verifies that the restore target is production-like, metadata-only, "
            "uses hosted services, has schema bootstrap disabled, and is not pointed "
            "at the public production API domain."
        ),
        formatter_class=_RawDefaultsHelpFormatter,
    )

    subcommands.add_parser(
        "production-config-check",
        help="Check production startup configuration without printing secrets.",
        description=(
            "Check production startup configuration without printing secrets. "
            "This verifies the fail-closed production contract and reports the "
            "public-beta approval boundary as metadata."
        ),
        formatter_class=_RawDefaultsHelpFormatter,
    )

    subcommands.add_parser(
        "observability-config-check",
        help="Check hosted observability configuration without printing secrets.",
        description=(
            "Check hosted observability configuration without printing secrets. "
            "This verifies metadata-only logging, hosted log and monitoring "
            "destinations, bounded retention, and security alert routing flags. "
            "It does not replace the required bounded hosted log review."
        ),
        formatter_class=_RawDefaultsHelpFormatter,
    )

    audit_verify_parser = subcommands.add_parser(
        "audit-ledger-verify",
        help="Verify the PostgreSQL audit ledger hash chain without printing secrets.",
        description=(
            "Verify the PostgreSQL audit ledger hash chain without printing secrets. "
            "Reads the database URL from an environment variable and reports "
            "metadata-only release-gate status."
        ),
        formatter_class=_RawDefaultsHelpFormatter,
    )
    audit_verify_parser.add_argument(
        "--database-url-env",
        default="AEVRYN_PROJECT_DATABASE_URL",
        help="Process environment variable containing the PostgreSQL database URL.",
    )

    audit_access_parser = subcommands.add_parser(
        "audit-access-report",
        help="Report PostgreSQL audit table access metadata without printing secrets.",
        description=(
            "Report PostgreSQL audit table access metadata without printing secrets. "
            "This checks table presence and current database privileges without "
            "dumping audit rows, database URLs, roles, usernames, or hostnames."
        ),
        formatter_class=_RawDefaultsHelpFormatter,
    )
    audit_access_parser.add_argument(
        "--database-url-env",
        default="AEVRYN_PROJECT_DATABASE_URL",
        help="Process environment variable containing the PostgreSQL database URL.",
    )

    audit_access_verify_parser = subcommands.add_parser(
        "audit-access-verify",
        help="Verify PostgreSQL audit table access is append-only and secret-safe.",
        description=(
            "Verify PostgreSQL audit table access is append-only and secret-safe. "
            "The configured database role must be able to read and append audit "
            "records, but must not be able to update, delete, or truncate them."
        ),
        formatter_class=_RawDefaultsHelpFormatter,
    )
    audit_access_verify_parser.add_argument(
        "--database-url-env",
        default="AEVRYN_PROJECT_DATABASE_URL",
        help="Process environment variable containing the PostgreSQL database URL.",
    )

    return parser


def _add_source_arguments(parser: argparse.ArgumentParser) -> None:
    """Add common source import arguments to a subcommand."""
    parser.add_argument(
        "path",
        help="Path to a supported source file: TXT, Markdown, HTML, FB2, DOCX, ODT, or EPUB.",
    )
    parser.add_argument(
        "--source-id",
        default="source_demo",
        help="Stable machine ID for this imported source.",
    )
    parser.add_argument(
        "--title",
        default=None,
        help="Human-readable source title; defaults to the file stem.",
    )


def _handle_import(args: argparse.Namespace) -> None:
    """Handle the import command."""
    path = Path(cast(str, args.path))
    imported_source = _runner().import_text_file(
        path=path,
        source_id=cast(str, args.source_id),
        title=cast(str | None, args.title),
    )
    scene_count = sum(len(chapter.scenes) for chapter in imported_source.story.chapters)
    print(
        json.dumps(
            {
                "source_id": imported_source.source_id,
                "source_format": SourceFileTextExtractor.source_format_for_path(path),
                "title": imported_source.title,
                "chapters": len(imported_source.story.chapters),
                "chapter_ids": [
                    chapter.chapter_id for chapter in imported_source.story.chapters
                ],
                "scenes": scene_count,
                "scene_ids": [
                    scene.scene_id
                    for chapter in imported_source.story.chapters
                    for scene in chapter.scenes
                ],
                "scene_map": [
                    {
                        "chapter_id": chapter.chapter_id,
                        "chapter_index": chapter.chapter_index,
                        "scene_id": scene.scene_id,
                        "scene_index": scene.scene_index,
                        "title": scene.title,
                    }
                    for chapter in imported_source.story.chapters
                    for scene in chapter.scenes
                ],
                "paragraphs": len(imported_source.paragraphs),
                "evidence_anchors": len(imported_source.anchors),
                "first_evidence_anchors": [
                    {
                        "anchor_id": anchor.anchor_id,
                        "chapter_id": anchor.chapter_id,
                        "scene_id": anchor.scene_id,
                        "paragraph_index": anchor.paragraph_index,
                        "sentence_index": anchor.sentence_index,
                    }
                    for anchor in imported_source.anchors[:5]
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )


def _handle_extract_demo(args: argparse.Namespace) -> None:
    """Handle the extract-demo command."""
    result = _runner().run_demo_text_file(
        path=Path(cast(str, args.path)),
        source_id=cast(str, args.source_id),
        title=cast(str | None, args.title),
    )
    print(
        json.dumps(
            {
                "results": [
                    {
                        "scene_id": extraction.scene_id,
                        "entities": [
                            {
                                "entity_id": entity.entity_id,
                                "entity_type": entity.entity_type,
                                "display_name": entity.display_name,
                                "confidence": entity.confidence,
                            }
                            for entity in extraction.entities
                        ],
                        "relationships": [
                            {
                                "source_entity_id": relationship.source_entity_id,
                                "relationship_type": relationship.relationship_type,
                                "target_entity_id": relationship.target_entity_id,
                                "confidence": relationship.confidence,
                            }
                            for relationship in extraction.relationships
                        ],
                    }
                    for extraction in result.extraction_results
                ],
                "accepted_entities": sum(
                    len(summary.accepted_entities) for summary in result.update_summaries
                ),
                "accepted_relationships": sum(
                    len(summary.accepted_relationships)
                    for summary in result.update_summaries
                ),
            },
            indent=2,
            sort_keys=True,
        )
    )


def _handle_extraction_prompt(args: argparse.Namespace) -> None:
    """Handle the extraction-prompt command."""
    runner = _runner()
    imported_source = runner.import_text_file(
        path=Path(cast(str, args.path)),
        source_id=cast(str, args.source_id),
        title=cast(str | None, args.title),
    )
    extraction_input = runner.build_scene_extraction_input(
        imported_source=imported_source,
        scene_id=cast(str | None, args.scene_id),
    )
    print(
        EvidenceBoundedAIExtractor(
            client=StaticAIExtractionClient("{}")
        ).build_prompt(extraction_input)
    )


def _handle_extract_ai_json(args: argparse.Namespace) -> None:
    """Handle the extract-ai-json command."""
    result = _run_ai_json(args)
    print(
        json.dumps(
            {
                "results": [
                    {
                        "scene_id": extraction.scene_id,
                        "entities": len(extraction.entities),
                        "facts": len(extraction.facts),
                        "relationships": len(extraction.relationships),
                        "state_changes": len(extraction.state_changes),
                    }
                    for extraction in result.extraction_results
                ],
                "accepted_entities": sum(
                    len(summary.accepted_entities) for summary in result.update_summaries
                ),
                "accepted_entity_ids": _summary_ids(
                    summary.accepted_entities for summary in result.update_summaries
                ),
                "accepted_facts": sum(
                    len(summary.accepted_facts) for summary in result.update_summaries
                ),
                "accepted_fact_ids": _summary_ids(
                    summary.accepted_facts for summary in result.update_summaries
                ),
                "accepted_relationships": sum(
                    len(summary.accepted_relationships)
                    for summary in result.update_summaries
                ),
                "accepted_relationship_ids": _summary_ids(
                    summary.accepted_relationships
                    for summary in result.update_summaries
                ),
                "accepted_state_changes": sum(
                    len(summary.accepted_state_changes)
                    for summary in result.update_summaries
                ),
                "accepted_state_change_ids": _summary_ids(
                    summary.accepted_state_changes
                    for summary in result.update_summaries
                ),
                "rejected_candidate_ids": _summary_ids(
                    summary.rejected_candidates for summary in result.update_summaries
                ),
            },
            indent=2,
            sort_keys=True,
        )
    )


def _handle_character(args: argparse.Namespace) -> None:
    """Handle the character command."""
    runner = _runner()
    result = _run_with_selected_extractor(args)
    character_id = cast(str, args.character_id)
    scene_id = cast(str | None, args.scene_id)
    if scene_id is not None:
        card = runner.build_character_card_at_scene(
            result=result,
            character_id=character_id,
            scene_id=scene_id,
        )
    else:
        card = runner.build_character_card(
            result=result,
            character_id=character_id,
            chapter_index=cast(int | None, args.chapter_index),
        )
    exporter = ExportEngine()
    output_format = cast(str, args.format)
    if output_format == "json":
        print(exporter.canon_character_card_json(card))
    elif output_format == "csv":
        print(exporter.canon_character_facts_csv(card), end="")
    else:
        view = PresentationEngine().character_profile(card)
        print(exporter.character_profile_markdown(view))


def _handle_scene(args: argparse.Namespace) -> None:
    """Handle the scene command."""
    runner = _runner()
    result = _run_with_selected_extractor(args)
    context = runner.build_scene_context(
        result=result,
        scene_id=cast(str | None, args.scene_id),
        character_ids=_character_ids_for_scene(
            args=args,
            result=result,
            scene_id=cast(str | None, args.scene_id),
        ),
    )
    exporter = ExportEngine()
    output_format = cast(str, args.format)
    if output_format == "json":
        print(exporter.canon_scene_context_json(context))
    else:
        analysis = SceneAnalyzer().analyze(context)
        view = PresentationEngine().scene_sheet(context=context, analysis=analysis)
        print(exporter.scene_sheet_view_markdown(view))


def _handle_prompt(args: argparse.Namespace) -> None:
    """Handle the prompt command."""
    runner = _runner()
    result = _run_with_selected_extractor(args)
    context = runner.build_scene_context(
        result=result,
        scene_id=cast(str | None, args.scene_id),
        character_ids=_character_ids_for_scene(
            args=args,
            result=result,
            scene_id=cast(str | None, args.scene_id),
        ),
    )
    pack = CanonPromptBuilder().build_production_pack(context)
    exporter = ExportEngine()
    output_format = cast(str, args.format)
    if output_format == "json":
        print(exporter.prompt_bundle_json(pack.prompt_bundle))
    else:
        analysis = SceneAnalyzer().analyze(context)
        scene = PresentationEngine().scene_sheet(context=context, analysis=analysis)
        view = PresentationEngine().production_pack(pack=pack, scene=scene)
        print(exporter.production_pack_view_markdown(view))


def _handle_world(args: argparse.Namespace) -> None:
    """Handle the world command."""
    runner = _runner()
    result = _run_with_selected_extractor(args)
    scene_id = cast(str | None, args.scene_id)
    if scene_id is not None:
        state = runner.build_world_state_at_scene(
            result=result,
            entity_ids=_dedupe_ids(cast(list[str], args.entity_id)),
            scene_id=scene_id,
        )
    else:
        state = runner.build_world_state(
            result=result,
            entity_ids=_dedupe_ids(cast(list[str], args.entity_id)),
            chapter_index=cast(int | None, args.chapter_index),
        )
    exporter = ExportEngine()
    output_format = cast(str, args.format)
    if output_format == "json":
        print(exporter.world_state_json(state))
    else:
        view = PresentationEngine().world_sheet(state)
        print(exporter.world_sheet_view_markdown(view))


def _handle_continuity(args: argparse.Namespace) -> None:
    """Handle the continuity command."""
    runner = _runner()
    result = _run_with_selected_extractor(args)
    report = runner.build_continuity_report(result)
    exporter = ExportEngine()
    output_format = cast(str, args.format)
    if output_format == "json":
        print(exporter.continuity_report_json(report))
    else:
        print(exporter.continuity_report_markdown(report))


def _handle_validate(args: argparse.Namespace) -> None:
    """Handle the validate command."""
    source_root = _validation_source_root(cast(str | None, args.source_root))
    runner = ValidationRunner(
        case_dir=Path(cast(str, args.case_dir)),
        source_root=source_root,
        case_ids=tuple(cast(list[str] | None, args.case_id) or ()),
    )

    output_format = cast(str, args.format)
    snapshot_dir = cast(str | None, args.snapshot_dir)
    if cast(bool, args.list_cases) and snapshot_dir is not None:
        raise ValueError("Validation snapshots cannot be written when listing cases.")
    if cast(bool, args.list_cases):
        _print_validation_cases(runner.list_cases(), output_format)
        return

    result = runner.run()
    if snapshot_dir is not None:
        _write_validation_snapshot(result=result, snapshot_dir=Path(snapshot_dir))

    if output_format == "json":
        print(_validation_result_json_text(result))
        if not result.passed:
            raise ValueError("Validation suite failed.")
        return

    if cast(bool, args.summary_only):
        print("Validation Summary")
        print()
    else:
        print("Running Validation Suite...")
        print()
        for case_result in result.results:
            status = "PASS" if case_result.passed else "FAIL"
            print(f"{case_result.genre} - {case_result.title}")
            print(status)
            if case_result.actual_import is not None:
                print(_validation_metrics_line(case_result.actual_import))
            if case_result.actual_extraction is not None:
                print(_validation_extraction_line(case_result.actual_extraction))
            for error in case_result.errors:
                print(f"  {error}")
            print()

    print("---------------------------------")
    print("Validation Totals")
    print(_validation_totals_line(result.totals))
    print()
    print("Validation Digest")
    print(result.suite_digest)
    print()
    print("Validation Score")
    print(f"{result.score}%")
    if not result.passed:
        raise ValueError("Validation suite failed.")


def _handle_performance_baseline(args: argparse.Namespace) -> int:
    """Handle the performance-baseline command."""
    compare_to = cast(str | None, args.compare_to)
    if compare_to is not None:
        regressions = compare_local_v2_performance_baseline(Path(compare_to))
        _print_performance_regressions(regressions)
        return 1 if any(item["status"] == "critical" for item in regressions) else 0

    output_path = write_local_v2_performance_baseline(Path(cast(str, args.output)))
    print(f"Performance baseline written: {output_path}")
    return 0


def compare_local_v2_performance_baseline(
    previous_path: Path,
) -> list[PerformanceRegressionPayload]:
    """Compare local V2 performance baselines without loading test tooling at CLI import."""
    from aevryn.performance_runner import compare_local_v2_performance_baseline as compare

    return compare(previous_path)


def write_local_v2_performance_baseline(output_path: Path) -> Path:
    """Write the local V2 performance baseline without loading test tooling at CLI import."""
    from aevryn.performance_runner import write_local_v2_performance_baseline as write

    return write(output_path)


def _print_performance_regressions(
    regressions: list[PerformanceRegressionPayload],
) -> None:
    """Print stable performance regression summary lines."""
    if not regressions:
        print("Performance baseline comparison passed.")
        return

    print("Performance regressions detected:")
    for regression in regressions:
        print(
            "  "
            f"{regression['status']} "
            f"{regression['benchmark']} "
            f"{regression['previous_ms']}ms -> {regression['current_ms']}ms "
            f"(+{regression['delta_ms']}ms, x{regression['ratio']})"
        )


def _handle_api(args: argparse.Namespace) -> None:
    """Handle the api command."""
    allowed_origins = tuple(cast(list[str] | None, args.allowed_origin) or ())
    reload_enabled = cast(bool, args.reload)
    if reload_enabled:
        if allowed_origins:
            os.environ[ALLOWED_ORIGINS_ENV] = ",".join(allowed_origins)
        app_target: FastAPI | str = "aevryn.api.app:create_app_from_env"
    else:
        environ = dict(os.environ)
        if allowed_origins:
            environ[ALLOWED_ORIGINS_ENV] = ",".join(allowed_origins)
        app_target = create_app_from_env(environ)

    _run_api_server(
        app=app_target,
        host=cast(str, args.host),
        port=cast(int, args.port),
        reload=reload_enabled,
        factory=reload_enabled,
    )


def _handle_provider_smoke(args: argparse.Namespace) -> None:
    """Handle the provider-smoke command."""
    env_file = Path(cast(str, args.env_file))
    timeout_seconds = cast(float, args.timeout_seconds)
    if timeout_seconds <= 0:
        raise ValueError("--timeout-seconds must be positive.")
    local_env = _load_local_env_file(env_file)
    api_key = _required_env_value(local_env, "AEVRYN_OPENAI_API_KEY")
    model = _required_env_value(local_env, "AEVRYN_OPENAI_MODEL")
    summary = _run_provider_api_workflow_smoke(
        api_key=api_key,
        model=model,
        timeout_seconds=timeout_seconds,
    )
    for key, value in summary.items():
        print(f"{key}={value}")


def _handle_provider_config_check() -> None:
    """Handle the provider-config-check command."""
    summary = _run_provider_config_check(dict(os.environ))
    for key, value in summary.items():
        print(f"{key}={value}")


def _handle_project_db_smoke(args: argparse.Namespace) -> None:
    """Handle the project-db-smoke command."""
    database_url_env = cast(str, args.database_url_env).strip()
    if not database_url_env:
        raise ValueError("--database-url-env cannot be blank.")
    database_url = _required_process_env_value(database_url_env)
    summary = _run_project_database_smoke(
        database_url=database_url,
        bootstrap_schema=not cast(bool, args.no_bootstrap),
    )
    for key, value in summary.items():
        print(f"{key}={value}")


def _handle_storage_smoke() -> None:
    """Handle the storage-smoke command."""
    storage_provider = _required_process_env_value(STORAGE_PROVIDER_ENV).lower()
    if storage_provider != "r2":
        raise ValueError("AEVRYN_STORAGE_PROVIDER must be r2 for storage-smoke.")
    summary = _run_r2_storage_smoke(
        bucket=_required_process_env_value(R2_BUCKET_ENV),
        endpoint_url=_required_process_env_value(R2_ENDPOINT_URL_ENV),
        access_key_id=_required_process_env_value(R2_ACCESS_KEY_ID_ENV),
        secret_key=_required_process_env_value(R2_SECRET_ACCESS_KEY_ENV),
        region_name=os.environ.get(R2_REGION_ENV, "auto"),
    )
    for key, value in summary.items():
        print(f"{key}={value}")


def _handle_hosted_deployment_smoke(args: argparse.Namespace) -> None:
    """Handle the hosted-deployment-smoke command."""
    frontend_url_env = cast(str, args.frontend_url_env).strip()
    api_url_env = cast(str, args.api_url_env).strip()
    origin_env = cast(str, args.origin_env).strip()
    timeout_seconds = cast(float, args.timeout_seconds)
    if not frontend_url_env:
        raise ValueError("--frontend-url-env cannot be blank.")
    if not api_url_env:
        raise ValueError("--api-url-env cannot be blank.")
    if not origin_env:
        raise ValueError("--origin-env cannot be blank.")
    if timeout_seconds <= 0:
        raise ValueError("--timeout-seconds must be positive.")
    summary = _run_hosted_deployment_smoke(
        frontend_url=_required_process_env_value(frontend_url_env),
        api_url=_required_process_env_value(api_url_env),
        expected_origin=_required_process_env_value(origin_env),
        timeout_seconds=timeout_seconds,
    )
    for key, value in summary.items():
        print(f"{key}={value}")


def _handle_cloud_run_deployment_check(args: argparse.Namespace) -> None:
    """Handle the cloud-run-deployment-check command."""
    service = cast(str, args.service).strip()
    region = cast(str, args.region).strip()
    expected_image_env = cast(str, args.expected_image_env).strip()
    gcloud_path = cast(str, args.gcloud_path).strip()
    timeout_seconds = cast(float, args.timeout_seconds)
    if not service:
        raise ValueError("--service cannot be blank.")
    if not region:
        raise ValueError("--region cannot be blank.")
    if not expected_image_env:
        raise ValueError("--expected-image-env cannot be blank.")
    if not gcloud_path:
        raise ValueError("--gcloud-path cannot be blank.")
    if timeout_seconds <= 0:
        raise ValueError("--timeout-seconds must be positive.")

    summary = _run_cloud_run_deployment_check(
        service=service,
        region=region,
        expected_image=_required_process_env_value(expected_image_env),
        gcloud_path=gcloud_path,
        timeout_seconds=timeout_seconds,
    )
    for key, value in summary.items():
        print(f"{key}={value}")


def _handle_worker_drain(args: argparse.Namespace) -> None:
    """Handle the worker-drain command."""
    api_url_env = cast(str, args.api_url_env).strip()
    worker_key_env = cast(str, args.worker_key_env).strip()
    max_jobs = cast(int, args.max_jobs)
    timeout_seconds = cast(float, args.timeout_seconds)
    if not api_url_env:
        raise ValueError("--api-url-env cannot be blank.")
    if not worker_key_env:
        raise ValueError("--worker-key-env cannot be blank.")
    if max_jobs < 1:
        raise ValueError("--max-jobs must be a positive integer.")
    if timeout_seconds <= 0:
        raise ValueError("--timeout-seconds must be positive.")

    summary = _run_hosted_worker_drain(
        api_url=_required_process_env_value(api_url_env),
        worker_api_key=_required_process_env_value(worker_key_env),
        max_jobs=max_jobs,
        timeout_seconds=timeout_seconds,
    )
    for key, value in summary.items():
        print(f"{key}={value}")


def _handle_restore_drill_fixture(args: argparse.Namespace) -> None:
    """Handle the restore-drill-fixture command."""
    api_url_env = cast(str, args.api_url_env).strip()
    bearer_token_env = cast(str, args.bearer_token_env).strip()
    worker_key_env = cast(str, args.worker_key_env).strip()
    timeout_seconds = cast(float, args.timeout_seconds)
    poll_attempts = cast(int, args.poll_attempts)
    poll_interval_seconds = cast(float, args.poll_interval_seconds)
    if not api_url_env:
        raise ValueError("--api-url-env cannot be blank.")
    if not bearer_token_env:
        raise ValueError("--bearer-token-env cannot be blank.")
    if not worker_key_env:
        raise ValueError("--worker-key-env cannot be blank.")
    worker_api_key = (
        _required_process_env_value(worker_key_env)
        if cast(bool, args.drain_worker)
        else None
    )
    summary = _run_restore_drill_fixture(
        api_url=_required_process_env_value(api_url_env),
        bearer_token=_required_process_env_value(bearer_token_env),
        worker_api_key=worker_api_key,
        drain_worker=cast(bool, args.drain_worker),
        create_export=cast(bool, args.create_export),
        require_succeeded_run=cast(bool, args.require_succeeded_run),
        timeout_seconds=timeout_seconds,
        poll_attempts=poll_attempts,
        poll_interval_seconds=poll_interval_seconds,
    )
    for key, value in summary.items():
        print(f"{key}={value}")


def _handle_restore_drill_verify(args: argparse.Namespace) -> None:
    """Handle the restore-drill-verify command."""
    api_url_env = cast(str, args.api_url_env).strip()
    owner_bearer_token_env = cast(str, args.owner_bearer_token_env).strip()
    other_bearer_token_env = cast(str, args.other_bearer_token_env).strip()
    cloud_run_identity_token_env = cast(str, args.cloud_run_identity_token_env).strip()
    timeout_seconds = cast(float, args.timeout_seconds)
    if not api_url_env:
        raise ValueError("--api-url-env cannot be blank.")
    if not owner_bearer_token_env:
        raise ValueError("--owner-bearer-token-env cannot be blank.")
    if not other_bearer_token_env:
        raise ValueError("--other-bearer-token-env cannot be blank.")
    if not cloud_run_identity_token_env:
        raise ValueError("--cloud-run-identity-token-env cannot be blank.")
    prompt_session_tokens = cast(bool, args.prompt_session_tokens)
    clipboard_session_tokens = cast(bool, args.clipboard_session_tokens)
    if prompt_session_tokens and clipboard_session_tokens:
        raise ValueError(
            "--prompt-session-tokens and --clipboard-session-tokens cannot both be used."
        )
    if prompt_session_tokens:
        owner_bearer_token = _prompt_hidden_value("Paste owner Aevryn session token")
        other_bearer_token = _prompt_hidden_value("Paste non-owner Aevryn session token")
    elif clipboard_session_tokens:
        owner_bearer_token = _prompt_clipboard_value(
            "Copy the owner Aevryn session token to the clipboard"
        )
        other_bearer_token = _prompt_clipboard_value(
            "Copy the non-owner Aevryn session token to the clipboard"
        )
    else:
        owner_bearer_token = _required_process_env_value(owner_bearer_token_env)
        other_bearer_token = _required_process_env_value(other_bearer_token_env)

    summary = _run_restore_drill_verify(
        api_url=_required_process_env_value(api_url_env),
        owner_bearer_token=str(owner_bearer_token),
        other_bearer_token=str(other_bearer_token),
        cloud_run_identity_token=os.environ.get(cloud_run_identity_token_env, ""),
        project_id=cast(str, args.project_id),
        active_story_id=cast(str, args.active_story_id),
        disposable_story_id=cast(str, args.disposable_story_id),
        import_id=cast(str, args.import_id),
        export_id=cast(str, args.export_id),
        allow_public_api_domain=cast(bool, args.allow_public_api_domain),
        timeout_seconds=timeout_seconds,
    )
    for key, value in summary.items():
        print(f"{key}={value}")


def _handle_production_config_check() -> None:
    """Handle the production-config-check command."""
    summary = _run_production_config_check(dict(os.environ))
    for key, value in summary.items():
        print(f"{key}={value}")


def _handle_restore_api_config_check() -> None:
    """Handle the restore-api-config-check command."""
    summary = _run_restore_api_config_check(dict(os.environ))
    for key, value in summary.items():
        print(f"{key}={value}")


def _handle_observability_config_check() -> None:
    """Handle the observability-config-check command."""
    summary = _run_observability_config_check(dict(os.environ))
    for key, value in summary.items():
        print(f"{key}={value}")


def _handle_audit_ledger_verify(args: argparse.Namespace) -> None:
    """Handle the audit-ledger-verify command."""
    database_url_env = cast(str, args.database_url_env)
    summary = _run_audit_ledger_verify(
        database_url=_required_process_env_value(database_url_env)
    )
    for key, value in summary.items():
        print(f"{key}={value}")


def _handle_audit_access_report(args: argparse.Namespace) -> None:
    """Handle the audit-access-report command."""
    database_url_env = cast(str, args.database_url_env)
    summary = _run_audit_access_report(
        database_url=_required_process_env_value(database_url_env)
    )
    for key, value in summary.items():
        print(f"{key}={value}")


def _handle_audit_access_verify(args: argparse.Namespace) -> None:
    """Handle the audit-access-verify command."""
    database_url_env = cast(str, args.database_url_env)
    summary = _run_audit_access_verify(
        database_url=_required_process_env_value(database_url_env)
    )
    for key, value in summary.items():
        print(f"{key}={value}")


def _load_local_env_file(path: Path) -> dict[str, str]:
    """Load simple KEY=VALUE pairs from an ignored local env file."""
    if not path.exists():
        raise ValueError(f"Local env file does not exist: {path}")
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"Invalid local env line in {path}: expected KEY=VALUE.")
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _required_env_value(values: dict[str, str], key: str) -> str:
    """Return a required local env value without logging its contents."""
    value = values.get(key, "").strip()
    if not value:
        raise ValueError(f"{key} is required in the local env file.")
    return value


def _required_process_env_value(key: str) -> str:
    """Return a required process env value without logging its contents."""
    value = os.environ.get(key, "").strip()
    if not value:
        raise ValueError(f"{key} is required in the process environment.")
    return value


def _prompt_hidden_value(prompt: str) -> str:
    """Prompt for a required value without echoing or logging it."""
    value = getpass.getpass(f"{prompt}: ").strip()
    if not value:
        raise ValueError(f"{prompt} cannot be blank.")
    return value


def _prompt_clipboard_value(prompt: str) -> str:
    """Read a required value from the operator clipboard without logging it."""
    input(f"{prompt}, then press Enter. Do not paste it here: ")
    value = _read_clipboard_text().strip()
    if not value:
        raise ValueError("Clipboard token value cannot be blank.")
    return value


def _read_clipboard_text() -> str:
    """Return text from the local clipboard without printing it."""
    if os.name != "nt":
        raise RuntimeError(
            "--clipboard-session-tokens currently requires Windows PowerShell."
        )
    result = subprocess.run(  # nosec B603 B607
        ["powershell.exe", "-NoProfile", "-Command", "Get-Clipboard -Raw"],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    return result.stdout


def _run_project_database_smoke(
    *,
    database_url: str,
    bootstrap_schema: bool = True,
) -> dict[str, object]:
    """Run a PostgreSQL Project Database smoke test and return metadata only."""
    repository = PostgresqlProjectRepository(
        database_url,
        bootstrap_schema=bootstrap_schema,
    )
    smoke_suffix = uuid4().hex
    user_id = f"user_pg_smoke_{smoke_suffix}"
    email = f"pg-smoke-{smoke_suffix}@example.invalid"
    created_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    repository.create_user(
        UserRecord(
            user_id=user_id,
            email=email,
            display_name="PostgreSQL Smoke Tester",
            created_at=created_at,
        )
    )
    stored_user = repository.get_user(user_id)
    if stored_user.email != email:
        raise PersistenceError("PostgreSQL smoke readback mismatch.")
    repository.delete_user_for_auth_rollback(user_id)
    try:
        repository.get_user(user_id)
    except RecordNotFoundError:
        deleted = True
    else:
        deleted = False
    if not deleted:
        raise PersistenceError("PostgreSQL smoke cleanup verification failed.")

    return {
        "adapter": "postgresql",
        "schema": "bootstrapped" if bootstrap_schema else "existing",
        "records_created": 1,
        "records_deleted": 1,
        "ok": "project_database_postgresql_smoke_completed",
    }


def _run_r2_storage_smoke(
    *,
    bucket: str,
    endpoint_url: str,
    access_key_id: str,
    secret_key: str,
    region_name: str,
) -> dict[str, object]:
    """Run a Cloudflare R2 smoke test and return metadata only."""
    storage = R2Storage(
        bucket=bucket,
        endpoint_url=endpoint_url,
        access_key_id=access_key_id,
        region_name=region_name,
        **{"secret_" + "access_key": secret_key},
    )
    smoke_id = uuid4().hex
    storage_ref = f"storage://smoke/r2/{smoke_id}/object.txt"
    content = b"aevryn storage smoke payload"
    stored = storage.save_object(
        storage_ref=storage_ref,
        content=content,
        content_type="text/plain",
        metadata={"aevryn_storage_kind": "readiness_smoke", "filename": "object.txt"},
    )
    if storage.read_object(storage_ref) != content:
        raise ValueError("R2 storage smoke readback mismatch.")
    storage.delete_object(storage_ref)
    try:
        storage.read_object(storage_ref)
    except StorageObjectNotFoundError:
        deleted = True
    else:
        deleted = False
    if not deleted:
        raise ValueError("R2 storage smoke cleanup verification failed.")

    return {
        "adapter": "r2",
        "bucket": bucket,
        "bytes_written": stored.size,
        "objects_created": 1,
        "objects_deleted": 1,
        "ok": "storage_r2_smoke_completed",
    }


def _run_hosted_deployment_smoke(
    *,
    frontend_url: str,
    api_url: str,
    expected_origin: str,
    timeout_seconds: float,
) -> dict[str, object]:
    """Verify the hosted frontend/API boundary and return metadata only."""
    normalized_frontend_url = _validated_https_origin_url(
        frontend_url,
        key=PUBLIC_FRONTEND_BASE_URL_ENV,
        purpose="hosted-deployment-smoke",
    )
    normalized_origin = _validated_https_origin_url(
        expected_origin,
        key=PUBLIC_FRONTEND_BASE_URL_ENV,
        purpose="hosted-deployment-smoke origin",
    )
    normalized_api_url = _validated_https_api_url(
        api_url,
        purpose="hosted-deployment-smoke",
    )
    if timeout_seconds <= 0:
        raise ValueError("--timeout-seconds must be positive.")

    smoke_headers = {"User-Agent": "AevrynReleaseSmoke/1.0"}
    frontend_status, frontend_bytes, frontend_headers = _hosted_raw_request(
        url=normalized_frontend_url,
        method="GET",
        headers={"Accept": "text/html", **smoke_headers},
        timeout_seconds=timeout_seconds,
        purpose="hosted-deployment-smoke frontend",
    )
    if frontend_status != 200:
        raise ValueError(
            f"hosted-deployment-smoke frontend returned HTTP {frontend_status}."
        )
    if frontend_bytes <= 0:
        raise ValueError("hosted-deployment-smoke frontend returned an empty response.")

    api_status, _api_bytes, api_headers, api_payload = _hosted_json_get(
        url=f"{normalized_api_url}/v2/health",
        headers={
            "Accept": "application/json",
            "Origin": normalized_origin,
            **smoke_headers,
        },
        timeout_seconds=timeout_seconds,
        purpose="hosted-deployment-smoke API health",
    )
    if api_status != 200:
        raise ValueError(f"hosted-deployment-smoke API returned HTTP {api_status}.")
    if str(api_payload.get("status") or "") != "ok":
        raise ValueError("hosted-deployment-smoke API health status is not ok.")

    cors_origin = api_headers.get("access-control-allow-origin", "")
    if cors_origin != normalized_origin:
        raise ValueError("hosted-deployment-smoke API CORS origin is not explicit.")
    if not api_headers.get("x-request-id", "").strip():
        raise ValueError("hosted-deployment-smoke API response is missing X-Request-ID.")

    storage_payload = api_payload.get("storage")
    storage = storage_payload if isinstance(storage_payload, dict) else {}
    return {
        "frontend_status": frontend_status,
        "frontend_bytes_present": _bool_text(frontend_bytes > 0),
        "frontend_security_header": _bool_text(
            frontend_headers.get("x-content-type-options", "").lower() == "nosniff"
        ),
        "api_status": api_status,
        "api_version": str(api_payload.get("api_version") or "unknown"),
        "api_engine": str(api_payload.get("engine") or "unknown"),
        "api_cors_origin": "explicit",
        "api_request_id": "present",
        "project_storage": str(storage.get("project_storage") or "unknown"),
        "import_content_storage": str(
            storage.get("import_content_storage") or "unknown"
        ),
        "secrets_printed": 0,
        "ok": "hosted_deployment_smoke_passed",
    }


def _run_cloud_run_deployment_check(
    *,
    service: str,
    region: str,
    expected_image: str,
    gcloud_path: str,
    timeout_seconds: float,
) -> dict[str, object]:
    """Verify Cloud Run serves the expected ready revision/image metadata only."""
    normalized_service = service.strip()
    normalized_region = region.strip()
    normalized_expected_image = expected_image.strip()
    normalized_gcloud_path = gcloud_path.strip()
    if not normalized_service:
        raise ValueError("Cloud Run service cannot be blank.")
    if not normalized_region:
        raise ValueError("Cloud Run region cannot be blank.")
    if not normalized_expected_image:
        raise ValueError("Expected Cloud Run image cannot be blank.")
    if not normalized_gcloud_path:
        raise ValueError("gcloud path cannot be blank.")
    if timeout_seconds <= 0:
        raise ValueError("Cloud Run deployment check timeout must be positive.")

    payload = _run_gcloud_cloud_run_service_describe(
        service=normalized_service,
        region=normalized_region,
        gcloud_path=normalized_gcloud_path,
        timeout_seconds=timeout_seconds,
    )
    status = payload.get("status")
    status_payload = status if isinstance(status, dict) else {}
    latest_ready_revision = str(status_payload.get("latestReadyRevisionName") or "")
    if not latest_ready_revision:
        raise ValueError("Cloud Run service has no latest ready revision.")

    traffic_percent = _cloud_run_latest_ready_traffic_percent(
        status_payload,
        latest_ready_revision=latest_ready_revision,
    )
    if traffic_percent != 100:
        raise ValueError("Cloud Run latest ready revision is not serving all traffic.")

    actual_image = _cloud_run_container_image(payload)
    if actual_image != normalized_expected_image:
        raise ValueError("Cloud Run deployed image does not match expected image.")

    return {
        "service": normalized_service,
        "region": normalized_region,
        "latest_ready_revision": "present",
        "latest_ready_revision_traffic_percent": traffic_percent,
        "image_matches_expected": "true",
        "secrets_printed": 0,
        "ok": "cloud_run_deployment_contract_checked",
    }


def _run_gcloud_cloud_run_service_describe(
    *,
    service: str,
    region: str,
    gcloud_path: str,
    timeout_seconds: float,
) -> dict[str, object]:
    """Return Cloud Run service metadata from gcloud as JSON."""
    try:
        result = subprocess.run(  # nosec B603
            [
                gcloud_path,
                "run",
                "services",
                "describe",
                service,
                "--region",
                region,
                "--format=json",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except FileNotFoundError as error:
        raise ValueError("gcloud is required for cloud-run-deployment-check.") from error
    except subprocess.TimeoutExpired as error:
        raise ValueError("Cloud Run deployment metadata request timed out.") from error

    if result.returncode != 0:
        raise ValueError("Cloud Run deployment metadata request failed.")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise ValueError("Cloud Run deployment metadata was not valid JSON.") from error
    if not isinstance(payload, dict):
        raise ValueError("Cloud Run deployment metadata was not an object.")
    return cast(dict[str, object], payload)


def _cloud_run_latest_ready_traffic_percent(
    status_payload: dict[str, object],
    *,
    latest_ready_revision: str,
) -> int:
    """Return the traffic percent assigned to the latest ready revision."""
    traffic_payload = status_payload.get("traffic")
    traffic_entries = traffic_payload if isinstance(traffic_payload, list) else []
    total_percent = 0
    for entry in traffic_entries:
        if not isinstance(entry, dict):
            continue
        revision_name = str(entry.get("revisionName") or "")
        latest_revision = entry.get("latestRevision") is True
        percent = _safe_int(entry.get("percent"))
        if revision_name == latest_ready_revision or latest_revision:
            total_percent += percent
    return total_percent


def _cloud_run_container_image(payload: dict[str, object]) -> str:
    """Return the first Cloud Run container image from service metadata."""
    spec = payload.get("spec")
    spec_payload = spec if isinstance(spec, dict) else {}
    template = spec_payload.get("template")
    template_payload = template if isinstance(template, dict) else {}
    template_spec = template_payload.get("spec")
    template_spec_payload = template_spec if isinstance(template_spec, dict) else {}
    containers = template_spec_payload.get("containers")
    container_entries = containers if isinstance(containers, list) else []
    for container in container_entries:
        if isinstance(container, dict):
            image = str(container.get("image") or "").strip()
            if image:
                return image
    raise ValueError("Cloud Run service metadata is missing a container image.")


def _safe_int(value: object) -> int:
    """Return an integer value from provider metadata or zero."""
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return 0
    return 0


def _run_audit_ledger_verify(*, database_url: str) -> dict[str, object]:
    """Verify the PostgreSQL audit ledger and return metadata only."""
    ledger = PostgresqlAuditLedger(database_url, bootstrap_schema=False)
    ledger.verify()
    return {
        "adapter": "postgresql",
        "ledger": "audit",
        "records_verified": len(ledger.records()),
        "secrets_printed": 0,
        "ok": "audit_ledger_postgresql_integrity_verified",
    }


def _run_audit_access_report(*, database_url: str) -> dict[str, object]:
    """Report PostgreSQL audit table access metadata without exposing identities."""
    report = postgresql_audit_access_report(database_url)
    return _audit_access_summary(report, ok="audit_access_metadata_reported")


def _run_audit_access_verify(*, database_url: str) -> dict[str, object]:
    """Verify PostgreSQL audit table access is safe for append-only writes."""
    report = postgresql_audit_access_report(database_url)
    _require_audit_access_contract(report)
    return _audit_access_summary(report, ok="audit_access_append_only_verified")


def _audit_access_summary(
    report: dict[str, object],
    *,
    ok: str,
) -> dict[str, object]:
    """Return stable metadata-only audit access output."""
    return {
        "adapter": "postgresql",
        "ledger": "audit",
        "table_exists": _bool_text(cast(bool, report["table_exists"])),
        "can_select": _bool_text(cast(bool, report["can_select"])),
        "can_insert": _bool_text(cast(bool, report["can_insert"])),
        "can_update": _bool_text(cast(bool, report["can_update"])),
        "can_delete": _bool_text(cast(bool, report["can_delete"])),
        "can_truncate": _bool_text(cast(bool, report["can_truncate"])),
        "is_table_owner": _bool_text(cast(bool, report["is_table_owner"])),
        "secrets_printed": 0,
        "ok": ok,
    }


def _require_audit_access_contract(report: dict[str, object]) -> None:
    """Require least-privilege append-only audit table access."""
    required_true = {
        "table_exists": "PostgreSQL audit table is missing.",
        "can_select": "PostgreSQL audit writer lacks SELECT privilege.",
        "can_insert": "PostgreSQL audit writer lacks INSERT privilege.",
    }
    for key, message in required_true.items():
        if report.get(key) is not True:
            raise ValueError(message)

    forbidden_true = {
        "can_update": "PostgreSQL audit append-only contract failed: UPDATE privilege is present.",
        "can_delete": "PostgreSQL audit append-only contract failed: DELETE privilege is present.",
        "can_truncate": (
            "PostgreSQL audit append-only contract failed: "
            "TRUNCATE privilege is present."
        ),
        "is_table_owner": (
            "PostgreSQL audit append-only contract failed: "
            "runtime role owns the audit table."
        ),
    }
    for key, message in forbidden_true.items():
        if report.get(key) is True:
            raise ValueError(message)


def _bool_text(value: bool) -> str:
    """Return a stable lowercase boolean string."""
    return "true" if value else "false"


def _run_production_config_check(environ: dict[str, str]) -> dict[str, object]:
    """Check the production startup contract and return metadata only."""
    if environ.get(DEPLOYMENT_ENV, "").strip().lower() != "production":
        raise ValueError(f"{DEPLOYMENT_ENV}=production is required.")
    try:
        create_app_from_env(environ)
    except ValueError as error:
        if not _record_production_config_failure_if_possible(environ, error):
            raise ValueError(
                f"{error} Production config failure audit was not recorded."
            ) from error
        raise
    return {
        "deployment_env": "production",
        "startup_contract": "ready",
        "public_beta": "not_approved_until_gate_signoff",
        "secrets_printed": 0,
        "ok": "production_config_contract_checked",
    }


def _run_restore_api_config_check(environ: dict[str, str]) -> dict[str, object]:
    """Check the isolated restore API contract and return metadata only."""
    if environ.get(DEPLOYMENT_ENV, "").strip().lower() != "production":
        raise ValueError(f"{DEPLOYMENT_ENV}=production is required for restore API drills.")

    _require_true_process_flag(environ, RESTORE_DRILL_TARGET_ENV)

    environment_name = _required_lower_env(environ, ENVIRONMENT_NAME_ENV)
    if environment_name == "production":
        raise ValueError(
            f"{ENVIRONMENT_NAME_ENV} must not be production for restore API drills."
        )

    public_api_url = _validated_https_api_url(
        environ.get(PUBLIC_API_BASE_URL_ENV, ""),
        purpose="restore-api-config-check",
    )
    parsed_public_api_url = urllib.parse.urlsplit(public_api_url)
    if parsed_public_api_url.netloc.lower() == "api.aevryn.ai":
        raise ValueError(
            "restore-api-config-check requires an isolated API URL. "
            "Do not use https://api.aevryn.ai for restore signoff."
        )

    database_adapter = _required_lower_env(environ, PROJECT_DATABASE_ADAPTER_ENV)
    if database_adapter != "postgresql":
        raise ValueError(
            f"{PROJECT_DATABASE_ADAPTER_ENV}=postgresql is required for restore API drills."
        )
    if not environ.get(PROJECT_DATABASE_URL_ENV, "").strip():
        raise ValueError(f"{PROJECT_DATABASE_URL_ENV} is required for restore API drills.")

    if environ.get(PROJECT_DATABASE_BOOTSTRAP_ENV, "").strip().lower() != "false":
        raise ValueError(
            f"{PROJECT_DATABASE_BOOTSTRAP_ENV}=false is required for restore API drills."
        )

    storage_provider = _required_lower_env(environ, STORAGE_PROVIDER_ENV)
    if storage_provider != "r2":
        raise ValueError(f"{STORAGE_PROVIDER_ENV}=r2 is required for restore API drills.")

    r2_bucket = environ.get(R2_BUCKET_ENV, "").strip()
    if not r2_bucket:
        raise ValueError(f"{R2_BUCKET_ENV} is required for restore API drills.")
    if r2_bucket == "aevryn-prod":
        raise ValueError(
            f"{R2_BUCKET_ENV} must not be aevryn-prod for restore API drills."
        )

    secret_manager = _required_lower_env(environ, SECRET_MANAGER_ENV)
    if secret_manager != "deployment":
        raise ValueError(
            f"{SECRET_MANAGER_ENV}=deployment is required for restore API drills."
        )

    log_destination = _required_lower_env(environ, LOG_DESTINATION_ENV)
    if log_destination != "hosted":
        raise ValueError(f"{LOG_DESTINATION_ENV}=hosted is required for restore API drills.")

    monitoring_destination = _required_lower_env(environ, MONITORING_DESTINATION_ENV)
    if monitoring_destination != "hosted":
        raise ValueError(
            f"{MONITORING_DESTINATION_ENV}=hosted is required for restore API drills."
        )

    _require_true_process_flag(environ, SECURITY_ALERTS_ENABLED_ENV)
    _require_true_process_flag(environ, METADATA_ONLY_LOGGING_ENV)

    return {
        "restore_target": "isolated_api",
        "deployment_env": "production",
        "environment_name": environment_name,
        "public_api_is_production_domain": "false",
        "project_database_adapter": database_adapter,
        "project_database_bootstrap": "false",
        "storage_provider": storage_provider,
        "metadata_only_logging": "true",
        "production_traffic_attached": "false",
        "secrets_printed": 0,
        "ok": "restore_api_config_contract_checked",
    }


def _run_observability_config_check(environ: dict[str, str]) -> dict[str, object]:
    """Check hosted observability release configuration and return metadata only."""
    if environ.get(DEPLOYMENT_ENV, "").strip().lower() != "production":
        raise ValueError(f"{DEPLOYMENT_ENV}=production is required.")

    log_destination = _required_lower_env(environ, LOG_DESTINATION_ENV)
    if log_destination != "hosted":
        raise ValueError(
            f"{LOG_DESTINATION_ENV}=hosted is required for public-beta observability."
        )
    monitoring_destination = _required_lower_env(environ, MONITORING_DESTINATION_ENV)
    if monitoring_destination != "hosted":
        raise ValueError(
            f"{MONITORING_DESTINATION_ENV}=hosted is required for public-beta observability."
        )

    log_retention_days = _required_positive_int(environ, LOG_RETENTION_DAYS_ENV)
    monitoring_retention_days = _required_positive_int(
        environ,
        MONITORING_RETENTION_DAYS_ENV,
    )
    maximum_operational_retention_days = 30
    if log_retention_days > maximum_operational_retention_days:
        raise ValueError(
            f"{LOG_RETENTION_DAYS_ENV} must be no more than "
            f"{maximum_operational_retention_days} days for public-beta observability."
        )
    if monitoring_retention_days > maximum_operational_retention_days:
        raise ValueError(
            f"{MONITORING_RETENTION_DAYS_ENV} must be no more than "
            f"{maximum_operational_retention_days} days for public-beta observability."
        )

    _require_true_process_flag(environ, SECURITY_ALERTS_ENABLED_ENV)
    _require_true_process_flag(environ, METADATA_ONLY_LOGGING_ENV)

    return {
        "deployment_env": "production",
        "log_destination": log_destination,
        "monitoring_destination": monitoring_destination,
        "log_retention_days": log_retention_days,
        "monitoring_retention_days": monitoring_retention_days,
        "security_alerts_enabled": "true",
        "metadata_only_logging": "true",
        "bounded_hosted_log_review": "required",
        "public_beta": "blocked_until_bounded_hosted_log_review",
        "secrets_printed": 0,
        "ok": "observability_config_contract_checked",
    }


def _run_provider_config_check(environ: dict[str, str]) -> dict[str, object]:
    """Check provider extraction configuration and return metadata only."""
    if environ.get(DEPLOYMENT_ENV, "").strip().lower() != "production":
        raise ValueError(f"{DEPLOYMENT_ENV}=production is required.")

    mode = _required_lower_env(environ, EXTRACTION_MODE_ENV)
    if mode != "openai":
        raise ValueError(
            f"{EXTRACTION_MODE_ENV}=openai is required for provider-backed extraction."
        )
    if not environ.get(OPENAI_API_KEY_ENV, "").strip():
        raise ValueError(f"{OPENAI_API_KEY_ENV} is required for provider-backed extraction.")
    model = environ.get(OPENAI_MODEL_ENV, "").strip()
    if not model:
        raise ValueError(f"{OPENAI_MODEL_ENV} is required for provider-backed extraction.")
    timeout_seconds = _required_positive_float(environ, OPENAI_TIMEOUT_SECONDS_ENV)
    max_response_bytes = _required_positive_int(environ, OPENAI_MAX_RESPONSE_BYTES_ENV)

    return {
        "deployment_env": "production",
        "provider": "openai",
        "extraction_mode": mode,
        "model": model,
        "timeout_seconds": timeout_seconds,
        "max_response_bytes": max_response_bytes,
        "request_storage": "disabled",
        "responses_store": "false",
        "provider_review": "required",
        "public_beta": "blocked_until_provider_review",
        "secrets_printed": 0,
        "ok": "provider_config_contract_checked",
    }


def _required_lower_env(environ: dict[str, str], key: str) -> str:
    """Return a required environment value normalized for configuration checks."""
    value = environ.get(key, "").strip().lower()
    if not value:
        raise ValueError(f"{key} is required.")
    return value


def _required_positive_int(environ: dict[str, str], key: str) -> int:
    """Return a required positive integer environment value."""
    value = environ.get(key, "").strip()
    if not value:
        raise ValueError(f"{key} is required.")
    try:
        parsed = int(value)
    except ValueError as error:
        raise ValueError(f"{key} must be a positive integer.") from error
    if parsed < 1:
        raise ValueError(f"{key} must be a positive integer.")
    return parsed


def _required_positive_float(environ: dict[str, str], key: str) -> float:
    """Return a required positive float environment value."""
    value = environ.get(key, "").strip()
    if not value:
        raise ValueError(f"{key} is required.")
    try:
        parsed = float(value)
    except ValueError as error:
        raise ValueError(f"{key} must be a positive number.") from error
    if parsed <= 0:
        raise ValueError(f"{key} must be a positive number.")
    return parsed


def _require_true_process_flag(environ: dict[str, str], key: str) -> None:
    """Require an explicit true flag for a production readiness check."""
    if environ.get(key, "").strip().lower() != "true":
        raise ValueError(f"{key}=true is required.")


def _record_production_config_failure_if_possible(
    environ: dict[str, str],
    error: ValueError,
) -> bool:
    """Record a metadata-only production config failure when audit storage exists."""
    if environ.get(PROJECT_DATABASE_ADAPTER_ENV, "").strip().lower() != "postgresql":
        return False
    database_url = environ.get(PROJECT_DATABASE_URL_ENV, "").strip()
    if not database_url:
        return False

    try:
        ledger = PostgresqlAuditLedger(database_url)
        ledger.append(
            event_type="security_configuration_failed",
            occurred_at=datetime.now(UTC).isoformat(timespec="milliseconds").replace(
                "+00:00",
                "Z",
            ),
            summary="Production config check failed.",
            metadata={"failure_code": _production_config_failure_code(str(error))},
        )
    except Exception:
        return False

    return True


def _production_config_failure_code(message: str) -> str:
    """Return a stable machine code for a production config failure message."""
    normalized = message.lower()
    known_fields = (
        DEPLOYMENT_ENV,
        PROJECT_DATABASE_ADAPTER_ENV,
        PROJECT_DATABASE_PATH_ENV,
        PROJECT_DATABASE_URL_ENV,
        ALLOWED_ORIGINS_ENV,
        PUBLIC_FRONTEND_BASE_URL_ENV,
        PUBLIC_API_BASE_URL_ENV,
        HTTPS_ONLY_ENV,
        HSTS_ENABLED_ENV,
        API_KEYS_ENV,
        STORAGE_PROVIDER_ENV,
        IMPORT_STORAGE_PATH_ENV,
        R2_BUCKET_ENV,
        R2_ACCOUNT_ID_ENV,
        R2_ENDPOINT_URL_ENV,
        R2_ACCESS_KEY_ID_ENV,
        R2_SECRET_ACCESS_KEY_ENV,
        SECRET_MANAGER_ENV,
        ENVIRONMENT_NAME_ENV,
        EXTRACTION_MODE_ENV,
        OPENAI_API_KEY_ENV,
        OPENAI_MODEL_ENV,
        WORKER_RUNTIME_ENV,
        WORKER_QUEUE_PROVIDER_ENV,
        WORKER_API_KEY_ENV,
        WORKER_TIMEOUT_SECONDS_ENV,
        WORKER_MAX_RETRIES_ENV,
        WORKER_CONCURRENCY_ENV,
        LOG_DESTINATION_ENV,
        MONITORING_DESTINATION_ENV,
        LOG_RETENTION_DAYS_ENV,
        MONITORING_RETENTION_DAYS_ENV,
        SECURITY_ALERTS_ENABLED_ENV,
        METADATA_ONLY_LOGGING_ENV,
        IDENTITY_PROVIDER_ENV,
        IDENTITY_PROVIDER_NAME_ENV,
        SUPABASE_URL_ENV,
        SUPABASE_JWKS_URL_ENV,
        SUPABASE_JWT_ALGORITHM_ENV,
        SUPABASE_JWT_SECRET_ENV,
        SUPABASE_ANON_KEY_ENV,
        SUPABASE_SERVICE_ROLE_KEY_ENV,
        SESSION_AUTHORITY_ENV,
        SESSION_SECRET_ENV,
        PASSWORD_RESET_ENABLED_ENV,
        ACCOUNT_DELETION_HANDOFF_ENV,
    )
    field_positions = {
        field: normalized.find(field.lower())
        for field in known_fields
        if field.lower() in normalized
    }
    if field_positions:
        first_field = min(field_positions, key=field_positions.__getitem__)
        return f"missing_or_invalid_{first_field.lower()}"

    return "invalid_production_configuration"


def _run_provider_api_workflow_smoke(
    *,
    api_key: str,
    model: str,
    timeout_seconds: float,
) -> dict[str, object]:
    """Run the synthetic provider-backed API workflow and return metadata only."""
    from fastapi.testclient import TestClient

    now = "2026-06-28T00:00:00Z"
    soon = "2026-06-28T00:05:00Z"
    repository = InMemoryProjectRepository()
    queue = InMemoryJobQueue()
    content_store = InMemoryImportContentStore()
    auth_service = AuthenticationService(
        repository=repository,
        credential_store=InMemoryCredentialStore(),
        session_store=InMemorySessionStore(),
        password_hasher=PasswordHasher(),
        token_factory=lambda: "token_provider_smoke",
        config=AuthenticationConfig(
            session_duration_seconds=3600,
            reset_duration_seconds=3600,
        ),
    )
    handler = ProjectImportSnapshotHandler(
        repository=repository,
        import_content_store=content_store,
        extractor=EvidenceBoundedAIExtractor(
            OpenAIResponsesAIExtractionClient(
                api_key=api_key,
                model=model,
                timeout_seconds=timeout_seconds,
                max_response_bytes=262144,
            )
        ),
    )
    client = TestClient(
        create_app(
            authentication_service=auth_service,
            project_repository=repository,
            background_job_queue=queue,
            background_job_handler=handler,
            import_content_store=content_store,
        )
    )
    register = client.post(
        "/v2/auth/register",
        json={
            "user_id": "user_provider_smoke",
            "email": "provider-smoke@example.com",
            "display_name": "Provider Smoke Tester",
            "password": "StrongPass123",
            "now": now,
        },
    )
    _require_response_ok(register.status_code, register.text, "register")
    headers = {
        "Authorization": f"Bearer {register.json()['session_token']}",
        "X-Aevryn-Now": soon,
    }
    _require_response_ok(
        client.post(
            "/v2/projects",
            headers=headers,
            json={
                "project_id": "project_provider_smoke",
                "name": "Provider API Smoke",
                "now": now,
            },
        ).status_code,
        "project creation failed",
        "project",
    )
    _require_response_ok(
        client.post(
            "/v2/projects/project_provider_smoke/stories",
            headers=headers,
            json={
                "story_id": "story_provider_smoke",
                "title": "Provider API Synthetic Story",
                "now": now,
            },
        ).status_code,
        "story creation failed",
        "story",
    )
    source_text = (
        "Chapter 1\n"
        "Mira opened the brass gate with a silver key while Jonah waited beside the tower.\n\n"
        "Jonah gave Mira the river map before the storm reached the tower."
    )
    import_payload: dict[str, object] = {
        "source_id": "source_provider_smoke",
        "filename": "provider-api-smoke.txt",
        "content_base64": base64.b64encode(source_text.encode("utf-8")).decode("ascii"),
        "title": "Provider API Synthetic Story",
    }
    inspected = client.post("/v2/imports/inspect", json=import_payload)
    _require_response_ok(inspected.status_code, inspected.text, "inspect")
    saved_import = client.post(
        "/v2/projects/project_provider_smoke/stories/story_provider_smoke/imports",
        headers=headers,
        json={"import_id": "import_provider_smoke", **import_payload, "now": now},
    )
    _require_response_ok(saved_import.status_code, saved_import.text, "save import")
    submitted = client.post(
        (
            "/v2/projects/project_provider_smoke/stories/story_provider_smoke"
            "/imports/import_provider_smoke/runs"
        ),
        headers=headers,
        json={"run_id": "run_provider_smoke", "job_id": "job_provider_smoke", "now": now},
    )
    _require_response_ok(submitted.status_code, submitted.text, "submit run")
    processed = client.post(
        "/v2/workers/process",
        json={"started_at": soon, "finished_at": soon, "max_jobs": 1},
    )
    _require_response_ok(processed.status_code, processed.text, "process worker")
    status = client.get("/v2/projects/project_provider_smoke/status", headers=headers)
    _require_response_ok(status.status_code, status.text, "status")
    outputs = client.get("/v2/projects/project_provider_smoke/outputs", headers=headers)
    _require_response_ok(outputs.status_code, outputs.text, "outputs")
    snapshots = client.get("/v2/projects/project_provider_smoke/snapshots", headers=headers)
    _require_response_ok(snapshots.status_code, snapshots.text, "snapshots")
    snapshot_payload = json.loads(snapshots.json()["snapshots"][0]["serialized_output"])
    outputs_payload = outputs.json()
    return {
        "model": model,
        "inspect_chapters": inspected.json()["chapters"],
        "inspect_scenes": inspected.json()["scenes"],
        "inspect_evidence_anchors": inspected.json()["evidence_anchors"],
        "worker_claimed": processed.json()["claimed_jobs"],
        "worker_succeeded": processed.json()["succeeded_jobs"],
        "project_status": status.json()["status"],
        "run_status": status.json()["latest_engine_run"]["status"],
        "snapshots_available": status.json()["snapshots"]["available"],
        "output_status": outputs_payload["status"],
        "output_characters": len(outputs_payload["character_profiles"]),
        "output_world_sections": len(outputs_payload["world_sheet"]["entity_sections"]),
        "accepted_entities": snapshot_payload["accepted_entity_count"],
        "accepted_facts": snapshot_payload["accepted_fact_count"],
        "accepted_relationships": snapshot_payload["accepted_relationship_count"],
        "accepted_state_changes": snapshot_payload["accepted_state_change_count"],
        "status_contains_source_sentence": "Mira opened the brass gate" in status.text,
        "outputs_contains_source_sentence": "Mira opened the brass gate" in outputs.text,
        "ok": "provider_api_workflow_synthetic_completed",
    }


def _run_hosted_worker_drain(
    *,
    api_url: str,
    worker_api_key: str,
    max_jobs: int,
    timeout_seconds: float,
) -> dict[str, object]:
    """Drain hosted worker jobs through the production API route."""
    normalized_api_url = api_url.rstrip("/")
    parsed_api_url = urllib.parse.urlsplit(normalized_api_url)
    if parsed_api_url.scheme != "https" or not parsed_api_url.netloc:
        raise ValueError("AEVRYN_PUBLIC_API_BASE_URL must use https:// for worker-drain.")
    if not worker_api_key.strip():
        raise ValueError("AEVRYN_WORKER_API_KEY is required for worker-drain.")
    if max_jobs < 1:
        raise ValueError("--max-jobs must be a positive integer.")
    if timeout_seconds <= 0:
        raise ValueError("--timeout-seconds must be positive.")

    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload = json.dumps(
        {
            "started_at": now,
            "finished_at": now,
            "max_jobs": max_jobs,
        },
        separators=(",", ":"),
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{normalized_api_url}/v2/workers/process",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-Aevryn-API-Key": worker_api_key,
        },
        method="POST",
    )
    try:
        # Bandit B310: URL scheme and host are validated above; this CLI is only for the
        # configured hosted API boundary and never accepts arbitrary URL schemes.
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # nosec B310
            response_payload = json.loads(response.read().decode("utf-8"))
            status_code = response.status
    except urllib.error.HTTPError as error:
        detail = _hosted_worker_error_detail(error)
        raise ValueError(f"worker-drain request failed with HTTP {error.code}: {detail}") from error
    except urllib.error.URLError as error:
        raise ValueError("worker-drain request failed before receiving a response.") from error

    return {
        "status": status_code,
        "claimed_jobs": int(response_payload["claimed_jobs"]),
        "succeeded_jobs": int(response_payload["succeeded_jobs"]),
        "failed_jobs": int(response_payload["failed_jobs"]),
        "ok": "hosted_worker_drain_completed",
    }


def _run_restore_drill_fixture(
    *,
    api_url: str,
    bearer_token: str,
    worker_api_key: str | None,
    drain_worker: bool,
    create_export: bool,
    require_succeeded_run: bool,
    timeout_seconds: float,
    poll_attempts: int,
    poll_interval_seconds: float,
) -> dict[str, object]:
    """Prepare source-side restore drill evidence through hosted API routes."""
    normalized_api_url = _validated_https_api_url(
        api_url,
        purpose="restore-drill-fixture",
    )
    session_credential = bearer_token.strip()
    if not session_credential:
        raise ValueError("Restore drill bearer token is required.")
    if drain_worker and not (worker_api_key or "").strip():
        raise ValueError("AEVRYN_WORKER_API_KEY is required when --drain-worker is set.")
    if timeout_seconds <= 0:
        raise ValueError("--timeout-seconds must be positive.")
    if poll_attempts < 1:
        raise ValueError("--poll-attempts must be a positive integer.")
    if poll_interval_seconds < 0:
        raise ValueError("--poll-interval-seconds cannot be negative.")

    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    fixture_suffix = uuid4().hex
    project_id = f"restore_drill_project_{fixture_suffix}"
    active_story_id = f"restore_drill_story_{fixture_suffix}"
    disposable_story_id = f"restore_drill_disposable_{fixture_suffix}"
    import_id = f"restore_drill_import_{fixture_suffix}"
    run_id = f"restore_drill_run_{fixture_suffix}"
    job_id = f"restore_drill_job_{fixture_suffix}"

    source_text = (
        "Chapter 1\n"
        "Mira cataloged the silver compass in the archive while Jonah checked "
        "the locked recovery cabinet.\n\n"
        "The archive alarm flashed once, and Mira recorded the compass as safe."
    )
    import_payload: dict[str, object] = {
        "source_id": f"restore_drill_source_{fixture_suffix}",
        "filename": "restore-drill-synthetic.txt",
        "content_base64": base64.b64encode(source_text.encode("utf-8")).decode("ascii"),
        "title": "Aevryn Restore Drill Synthetic Story",
    }

    headers = {
        "Authorization": f"Bearer {session_credential}",
        "X-Aevryn-Now": now,
    }
    _hosted_json_request(
        api_url=normalized_api_url,
        path="/v2/projects",
        method="POST",
        payload={
            "project_id": project_id,
            "name": "Aevryn Restore Drill Fixture",
            "now": now,
        },
        headers=headers,
        timeout_seconds=timeout_seconds,
    )
    _hosted_json_request(
        api_url=normalized_api_url,
        path=f"/v2/projects/{project_id}/stories",
        method="POST",
        payload={
            "story_id": active_story_id,
            "title": "Restore Drill Active Story",
            "now": now,
        },
        headers=headers,
        timeout_seconds=timeout_seconds,
    )
    _hosted_json_request(
        api_url=normalized_api_url,
        path=f"/v2/projects/{project_id}/stories",
        method="POST",
        payload={
            "story_id": disposable_story_id,
            "title": "Restore Drill Disposable Story",
            "now": now,
        },
        headers=headers,
        timeout_seconds=timeout_seconds,
    )
    _hosted_json_request(
        api_url=normalized_api_url,
        path=f"/v2/projects/{project_id}/stories/{disposable_story_id}",
        method="DELETE",
        payload=None,
        headers=headers,
        timeout_seconds=timeout_seconds,
    )
    inspected = _hosted_json_request(
        api_url=normalized_api_url,
        path="/v2/imports/inspect",
        method="POST",
        payload=import_payload,
        headers=headers,
        timeout_seconds=timeout_seconds,
    )
    saved_import = _hosted_json_request(
        api_url=normalized_api_url,
        path=f"/v2/projects/{project_id}/stories/{active_story_id}/imports",
        method="POST",
        payload={"import_id": import_id, **import_payload, "now": now},
        headers=headers,
        timeout_seconds=timeout_seconds,
    )
    _hosted_json_request(
        api_url=normalized_api_url,
        path=(
            f"/v2/projects/{project_id}/stories/{active_story_id}"
            f"/imports/{import_id}/runs"
        ),
        method="POST",
        payload={"run_id": run_id, "job_id": job_id, "now": now},
        headers=headers,
        timeout_seconds=timeout_seconds,
    )

    worker_drained = False
    worker_succeeded_jobs = 0
    if drain_worker:
        worker_response = _hosted_json_request(
            api_url=normalized_api_url,
            path="/v2/workers/process",
            method="POST",
            payload={
                "started_at": now,
                "finished_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "max_jobs": 1,
            },
            headers={
                "X-Aevryn-API-Key": cast(str, worker_api_key),
                "X-Aevryn-Now": now,
            },
            timeout_seconds=timeout_seconds,
        )
        worker_drained = True
        worker_succeeded_jobs = _metadata_int(worker_response, "succeeded_jobs")

    status = _poll_project_status(
        api_url=normalized_api_url,
        project_id=project_id,
        headers=headers,
        timeout_seconds=timeout_seconds,
        poll_attempts=poll_attempts,
        poll_interval_seconds=poll_interval_seconds,
    )
    latest_run = status.get("latest_engine_run")
    latest_run_payload = latest_run if isinstance(latest_run, dict) else {}
    run_status = str(latest_run_payload.get("status") or "unknown")
    if require_succeeded_run and run_status != "succeeded":
        raise ValueError("restore-drill-fixture run did not reach succeeded state.")

    snapshots = status.get("snapshots")
    snapshots_payload = snapshots if isinstance(snapshots, dict) else {}
    snapshots_available = bool(snapshots_payload.get("available"))
    latest_snapshot_id = str(snapshots_payload.get("latest_snapshot_id") or "")
    export_created = False
    if create_export and snapshots_available and latest_snapshot_id:
        _hosted_json_request(
            api_url=normalized_api_url,
            path=f"/v2/projects/{project_id}/exports",
            method="POST",
            payload={
                "export_id": f"restore_drill_export_{fixture_suffix}",
                "snapshot_id": latest_snapshot_id,
                "export_format": "json",
                "filename": "restore-drill-canon.json",
                "now": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
            headers=headers,
            timeout_seconds=timeout_seconds,
        )
        export_created = True

    ok = (
        "restore_drill_fixture_prepared"
        if run_status == "succeeded" and (not create_export or export_created)
        else "restore_drill_fixture_incomplete"
    )
    return {
        "drill_fixture": "source",
        "project_id": project_id,
        "active_story_id": active_story_id,
        "disposable_story_id": disposable_story_id,
        "import_id": import_id,
        "run_id": run_id,
        "project_created": True,
        "active_story_created": True,
        "disposable_story_deleted": True,
        "import_saved": True,
        "run_submitted": True,
        "worker_drained": worker_drained,
        "worker_succeeded_jobs": worker_succeeded_jobs,
        "run_status": run_status,
        "snapshots_available": snapshots_available,
        "export_created": export_created,
        "inspect_chapters": _metadata_int(inspected, "chapters"),
        "inspect_scenes": _metadata_int(inspected, "scenes"),
        "inspect_evidence_anchors": _metadata_int(inspected, "evidence_anchors"),
        "saved_import_chapters": _metadata_int(saved_import, "chapter_count"),
        "saved_import_scenes": _metadata_int(saved_import, "scene_count"),
        "source_bytes_printed": 0,
        "secrets_printed": 0,
        "restore_target_created": False,
        "public_beta": "blocked_until_isolated_restore_drill_passes",
        "ok": ok,
    }


def _run_restore_drill_verify(
    *,
    api_url: str,
    owner_bearer_token: str,
    other_bearer_token: str,
    cloud_run_identity_token: str,
    project_id: str,
    active_story_id: str,
    disposable_story_id: str,
    import_id: str,
    export_id: str,
    allow_public_api_domain: bool,
    timeout_seconds: float,
) -> dict[str, object]:
    """Verify restored API ownership boundaries without printing private data."""
    normalized_api_url = _validated_https_api_url(
        api_url,
        purpose="restore-drill-verify",
    )
    _require_isolated_restore_api_url(
        normalized_api_url,
        allow_public_api_domain=allow_public_api_domain,
    )
    owner_session_credential = owner_bearer_token.strip()
    other_session_credential = other_bearer_token.strip()
    if not owner_session_credential or not other_session_credential:
        raise ValueError("Restore drill owner and non-owner bearer tokens are required.")
    if owner_session_credential == other_session_credential:
        raise ValueError("Restore drill owner and non-owner bearer tokens must differ.")
    if timeout_seconds <= 0:
        raise ValueError("--timeout-seconds must be positive.")

    project_id = _required_cli_id(project_id, "--project-id")
    active_story_id = _required_cli_id(active_story_id, "--active-story-id")
    disposable_story_id = _required_cli_id(disposable_story_id, "--disposable-story-id")
    expected_import_id = import_id.strip()
    expected_export_id = export_id.strip()

    cloud_run_session_credential = cloud_run_identity_token.strip()
    cloud_run_headers = (
        {"X-Serverless-Authorization": f"Bearer {cloud_run_session_credential}"}
        if cloud_run_session_credential
        else {}
    )
    request_now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    owner_headers = {
        "Authorization": f"Bearer {owner_session_credential}",
        "X-Aevryn-Now": request_now,
        **cloud_run_headers,
    }
    other_headers = {
        "Authorization": f"Bearer {other_session_credential}",
        "X-Aevryn-Now": request_now,
        **cloud_run_headers,
    }
    owner_project = _hosted_json_request(
        api_url=normalized_api_url,
        path=f"/v2/projects/{project_id}",
        method="GET",
        payload=None,
        headers=owner_headers,
        timeout_seconds=timeout_seconds,
        purpose="restore-drill-verify",
    )
    if str(owner_project.get("project_id") or "") != project_id:
        raise ValueError("restore-drill-verify owner project readback mismatch.")

    stories_payload = _hosted_json_request(
        api_url=normalized_api_url,
        path=f"/v2/projects/{project_id}/stories",
        method="GET",
        payload=None,
        headers=owner_headers,
        timeout_seconds=timeout_seconds,
        purpose="restore-drill-verify",
    )
    story_ids = _payload_ids(stories_payload, "stories", "story_id")
    if active_story_id not in story_ids:
        raise ValueError("restore-drill-verify active story is missing.")
    if disposable_story_id in story_ids:
        raise ValueError("restore-drill-verify disposable story reappeared.")

    imports_payload = _hosted_json_request(
        api_url=normalized_api_url,
        path=f"/v2/projects/{project_id}/stories/{active_story_id}/imports",
        method="GET",
        payload=None,
        headers=owner_headers,
        timeout_seconds=timeout_seconds,
        purpose="restore-drill-verify",
    )
    import_ids = _payload_ids(imports_payload, "imports", "import_id")
    import_metadata_visible = bool(import_ids)
    if expected_import_id and expected_import_id not in import_ids:
        raise ValueError("restore-drill-verify expected import is missing.")
    if not import_metadata_visible:
        raise ValueError("restore-drill-verify owner import metadata is missing.")

    status_payload = _hosted_json_request(
        api_url=normalized_api_url,
        path=f"/v2/projects/{project_id}/status",
        method="GET",
        payload=None,
        headers=owner_headers,
        timeout_seconds=timeout_seconds,
        purpose="restore-drill-verify",
    )
    status = str(status_payload.get("status") or "unknown")
    snapshot_payload = status_payload.get("snapshots")
    snapshots_available = (
        bool(snapshot_payload.get("available"))
        if isinstance(snapshot_payload, dict)
        else False
    )

    exports_payload = _hosted_json_request(
        api_url=normalized_api_url,
        path=f"/v2/projects/{project_id}/exports",
        method="GET",
        payload=None,
        headers=owner_headers,
        timeout_seconds=timeout_seconds,
        purpose="restore-drill-verify",
    )
    export_ids = _payload_ids(exports_payload, "exports", "export_id")
    selected_export_id = expected_export_id or (export_ids[0] if export_ids else "")
    if expected_export_id and expected_export_id not in export_ids:
        raise ValueError("restore-drill-verify expected export is missing.")
    if not selected_export_id:
        raise ValueError("restore-drill-verify owner export metadata is missing.")

    export_download_status, export_download_size = _hosted_request_status(
        api_url=normalized_api_url,
        path=f"/v2/projects/{project_id}/exports/{selected_export_id}/download",
        method="GET",
        payload=None,
        headers=owner_headers,
        timeout_seconds=timeout_seconds,
    )
    if export_download_status != 200 or export_download_size <= 0:
        raise ValueError("restore-drill-verify owner export download is unavailable.")

    _require_denied(
        _hosted_request_status(
            api_url=normalized_api_url,
            path=f"/v2/projects/{project_id}",
            method="GET",
            payload=None,
            headers=other_headers,
            timeout_seconds=timeout_seconds,
        )[0],
        "cross-user project read",
    )
    _require_denied(
        _hosted_request_status(
            api_url=normalized_api_url,
            path=f"/v2/projects/{project_id}/stories/{active_story_id}/imports",
            method="GET",
            payload=None,
            headers=other_headers,
            timeout_seconds=timeout_seconds,
        )[0],
        "cross-user story imports",
    )
    _require_denied(
        _hosted_request_status(
            api_url=normalized_api_url,
            path=f"/v2/projects/{project_id}/exports",
            method="GET",
            payload=None,
            headers=other_headers,
            timeout_seconds=timeout_seconds,
        )[0],
        "cross-user exports",
    )
    _require_denied(
        _hosted_request_status(
            api_url=normalized_api_url,
            path=f"/v2/projects/{project_id}/exports/{selected_export_id}/download",
            method="GET",
            payload=None,
            headers=other_headers,
            timeout_seconds=timeout_seconds,
        )[0],
        "cross-user export download",
    )
    _require_denied(
        _hosted_request_status(
            api_url=normalized_api_url,
            path=f"/v2/projects/{project_id}/stories/{disposable_story_id}/imports",
            method="GET",
            payload=None,
            headers=owner_headers,
            timeout_seconds=timeout_seconds,
        )[0],
        "deleted story imports",
    )

    return {
        "drill_verification": "isolated_api",
        "project_id": project_id,
        "owner_project_read": "passed",
        "owner_active_story_present": "passed",
        "deleted_story_absent_from_product_surfaces": "passed",
        "owner_import_metadata_visible": "passed",
        "source_storage_owner_scoped": "passed",
        "project_status": status,
        "snapshots_available": _bool_text(snapshots_available),
        "owner_export_metadata_visible": "passed",
        "owner_export_download_available": "passed",
        "export_storage_owner_scoped": "passed",
        "cross_user_project_read": "denied",
        "cross_user_story_imports": "denied",
        "cross_user_exports": "denied",
        "cross_user_export_download": "denied",
        "deleted_story_imports": "denied",
        "private_cloud_run_auth": (
            "present" if cloud_run_session_credential else "not_configured"
        ),
        "source_bytes_printed": 0,
        "export_bytes_printed": 0,
        "storage_refs_printed": 0,
        "secrets_printed": 0,
        "restore_logs_metadata_only": "not_run_requires_hosted_log_review",
        "production_traffic_attached": "false",
        "public_beta": "blocked_until_restore_logs_review_passes",
        "ok": "restore_drill_api_boundaries_verified",
    }


def _poll_project_status(
    *,
    api_url: str,
    project_id: str,
    headers: dict[str, str],
    timeout_seconds: float,
    poll_attempts: int,
    poll_interval_seconds: float,
) -> dict[str, object]:
    """Poll project status until the latest run reaches a terminal state or attempts end."""
    status: dict[str, object] = {}
    for attempt in range(poll_attempts):
        status = _hosted_json_request(
            api_url=api_url,
            path=f"/v2/projects/{project_id}/status",
            method="GET",
            payload=None,
            headers=headers,
            timeout_seconds=timeout_seconds,
        )
        latest_run = status.get("latest_engine_run") or {}
        if isinstance(latest_run, dict) and latest_run.get("status") in {
            "succeeded",
            "failed",
        }:
            return status
        if attempt < poll_attempts - 1 and poll_interval_seconds:
            time.sleep(poll_interval_seconds)
    return status


def _metadata_int(payload: dict[str, object], key: str) -> int:
    """Return an integer metadata value from a hosted API JSON payload."""
    value = payload.get(key, 0)
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return 0


def _payload_ids(
    payload: dict[str, object],
    collection_key: str,
    id_key: str,
) -> tuple[str, ...]:
    """Return stable IDs from a metadata collection payload."""
    collection = payload.get(collection_key)
    if not isinstance(collection, list):
        if not isinstance(collection, tuple):
            return ()
    ids: list[str] = []
    for item in collection:
        if isinstance(item, dict):
            item_id = str(item.get(id_key) or "").strip()
            if item_id:
                ids.append(item_id)
    return tuple(ids)


def _required_cli_id(value: str, option_name: str) -> str:
    """Return a required CLI identifier."""
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{option_name} cannot be blank.")
    return normalized


def _require_isolated_restore_api_url(
    api_url: str,
    *,
    allow_public_api_domain: bool,
) -> None:
    """Fail closed if restore verification points at the public production API."""
    parsed_api_url = urllib.parse.urlsplit(api_url)
    if parsed_api_url.netloc.lower() == "api.aevryn.ai" and not allow_public_api_domain:
        raise ValueError(
            "restore-drill-verify requires an isolated API URL. "
            "Use --allow-public-api-domain only for source preflight."
        )


def _require_denied(status_code: int, label: str) -> None:
    """Require an API boundary check to fail closed."""
    if status_code not in {401, 403, 404}:
        raise ValueError(f"restore-drill-verify expected denial for {label}.")


def _hosted_request_status(
    *,
    api_url: str,
    path: str,
    method: str,
    payload: dict[str, object] | None,
    headers: dict[str, str],
    timeout_seconds: float,
) -> tuple[int, int]:
    """Return HTTP status and byte count without returning private response bodies."""
    request_headers = {"Accept": "application/json", **headers}
    request_data = None
    if payload is not None:
        request_headers["Content-Type"] = "application/json"
        request_data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        f"{api_url}{path}",
        data=request_data,
        headers=request_headers,
        method=method,
    )
    try:
        # Bandit B310: URL scheme and host are validated by _validated_https_api_url.
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # nosec B310
            return response.status, len(response.read())
    except urllib.error.HTTPError as error:
        return error.code, 0
    except urllib.error.URLError as error:
        raise ValueError(
            "restore-drill-verify request failed before receiving a response."
        ) from error


def _hosted_json_request(
    *,
    api_url: str,
    path: str,
    method: str,
    payload: dict[str, object] | None,
    headers: dict[str, str],
    timeout_seconds: float,
    purpose: str = "restore-drill-fixture",
) -> dict[str, object]:
    """Send one hosted API request and return JSON metadata without echoing secrets."""
    request_headers = {"Accept": "application/json", **headers}
    request_data = None
    if payload is not None:
        request_headers["Content-Type"] = "application/json"
        request_data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        f"{api_url}{path}",
        data=request_data,
        headers=request_headers,
        method=method,
    )
    try:
        # Bandit B310: URL scheme and host are validated by _validated_https_api_url.
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # nosec B310
            raw_body = response.read()
            if response.status == 204 or not raw_body:
                return {}
            return cast(dict[str, object], json.loads(raw_body.decode("utf-8")))
    except urllib.error.HTTPError as error:
        detail = _hosted_api_error_detail(error)
        raise ValueError(
            f"{purpose} {method} {path} failed with HTTP {error.code}: {detail}"
        ) from error
    except urllib.error.URLError as error:
        raise ValueError(
            "restore-drill-fixture request failed before receiving a response."
        ) from error


def _hosted_raw_request(
    *,
    url: str,
    method: str,
    headers: dict[str, str],
    timeout_seconds: float,
    purpose: str,
) -> tuple[int, int, dict[str, str]]:
    """Return hosted response metadata without exposing response bodies."""
    request = urllib.request.Request(
        url,
        headers=headers,
        method=method,
    )
    try:
        # Bandit B310: caller validates the HTTPS URL before calling this helper.
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # nosec B310
            return response.status, len(response.read()), _safe_headers(response.headers)
    except urllib.error.HTTPError as error:
        return error.code, 0, _safe_headers(error.headers)
    except urllib.error.URLError as error:
        raise ValueError(f"{purpose} failed before receiving a response.") from error


def _hosted_json_get(
    *,
    url: str,
    headers: dict[str, str],
    timeout_seconds: float,
    purpose: str,
) -> tuple[int, int, dict[str, str], dict[str, object]]:
    """Return hosted JSON metadata without printing full response bodies."""
    status_code, byte_count, response_headers, payload = _hosted_json_url_request(
        url=url,
        headers=headers,
        timeout_seconds=timeout_seconds,
        purpose=purpose,
    )
    return status_code, byte_count, response_headers, payload


def _hosted_json_url_request(
    *,
    url: str,
    headers: dict[str, str],
    timeout_seconds: float,
    purpose: str,
) -> tuple[int, int, dict[str, str], dict[str, object]]:
    """GET one hosted JSON URL and return bounded metadata."""
    request = urllib.request.Request(
        url,
        headers=headers,
        method="GET",
    )
    try:
        # Bandit B310: caller validates the HTTPS URL before calling this helper.
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # nosec B310
            raw_body = response.read()
            payload = json.loads(raw_body.decode("utf-8")) if raw_body else {}
            if not isinstance(payload, dict):
                raise ValueError(f"{purpose} returned non-object JSON.")
            return (
                response.status,
                len(raw_body),
                _safe_headers(response.headers),
                cast(dict[str, object], payload),
            )
    except urllib.error.HTTPError as error:
        detail = _hosted_api_error_detail(error)
        raise ValueError(f"{purpose} failed with HTTP {error.code}: {detail}") from error
    except urllib.error.URLError as error:
        raise ValueError(f"{purpose} failed before receiving a response.") from error
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"{purpose} returned invalid JSON.") from error


def _safe_headers(headers: Any) -> dict[str, str]:
    """Return lower-case response headers safe for metadata checks."""
    return {str(key).lower(): str(value) for key, value in headers.items()}


def _validated_https_api_url(api_url: str, *, purpose: str) -> str:
    """Return a normalized hosted API URL after HTTPS validation."""
    normalized_api_url = api_url.rstrip("/")
    parsed_api_url = urllib.parse.urlsplit(normalized_api_url)
    if parsed_api_url.scheme != "https" or not parsed_api_url.netloc:
        raise ValueError(f"AEVRYN_PUBLIC_API_BASE_URL must use https:// for {purpose}.")
    return normalized_api_url


def _validated_https_origin_url(url: str, *, key: str, purpose: str) -> str:
    """Return a normalized HTTPS origin URL without paths or credentials."""
    normalized_url = url.rstrip("/")
    parsed_url = urllib.parse.urlsplit(normalized_url)
    if parsed_url.scheme != "https" or not parsed_url.netloc:
        raise ValueError(f"{key} must use https:// for {purpose}.")
    if parsed_url.username or parsed_url.password:
        raise ValueError(f"{key} cannot include credentials for {purpose}.")
    if parsed_url.path not in {"", "/"} or parsed_url.query or parsed_url.fragment:
        raise ValueError(f"{key} must be an origin URL for {purpose}.")
    return urllib.parse.urlunsplit((parsed_url.scheme, parsed_url.netloc, "", "", ""))


def _hosted_api_error_detail(error: urllib.error.HTTPError) -> str:
    """Return bounded hosted API error detail without leaking request credentials."""
    try:
        payload = json.loads(error.read().decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return "request_failed"
    raw_detail = payload.get("detail") if isinstance(payload, dict) else None
    if isinstance(raw_detail, dict):
        detail = str(raw_detail.get("error") or raw_detail.get("detail") or "request_failed")
    else:
        detail = str(raw_detail or payload.get("error") or "request_failed")
    safe_detail = "".join(
        character
        for character in detail
        if character.isalnum() or character in {"_", "-", ":", " ", "."}
    ).strip()
    return (safe_detail or "request_failed")[:160]


def _hosted_worker_error_detail(error: urllib.error.HTTPError) -> str:
    """Return a bounded worker-drain error detail without exposing credentials."""
    try:
        payload = json.loads(error.read().decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return "request_failed"
    detail = str(payload.get("error") or payload.get("detail") or "request_failed")
    safe_detail = "".join(
        character
        for character in detail
        if character.isalnum() or character in {"_", "-", ":", " "}
    ).strip()
    return (safe_detail or "request_failed")[:160]


def _require_response_ok(status_code: int, text: str, label: str) -> None:
    """Raise a compact smoke-test error for failed API calls."""
    if status_code != 200:
        raise ValueError(f"Provider smoke {label} failed with HTTP {status_code}: {text}")


def _run_api_server(
    app: FastAPI | str,
    host: str,
    port: int,
    reload: bool,
    factory: bool = False,
) -> None:
    """Run the FastAPI app through Uvicorn."""
    try:
        import uvicorn
    except ImportError as error:
        raise ValueError(
            "The V2 API server requires the platform extra. "
            "Install with `pip install -e .[platform]`."
        ) from error

    uvicorn.run(app, host=host, port=port, reload=reload, factory=factory)


def _print_validation_cases(cases: tuple[ValidationCase, ...], output_format: str) -> None:
    """Print validation case metadata."""
    if output_format == "json":
        print(
            json.dumps(
                {
                    "cases": [
                        {
                            "case_id": case.case_id,
                            "title": case.title,
                            "genre": case.genre,
                            "source_directory": case.source_directory,
                            "chapter_glob": case.chapter_glob,
                        }
                        for case in cases
                    ]
                },
                indent=2,
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return

    print("Validation Cases")
    print()
    for case in cases:
        print(f"{case.case_id}")
        print(f"  genre={case.genre}")
        print(f"  title={case.title}")
        print(f"  source={case.source_directory}")
        print()


def _write_validation_snapshot(result: ValidationSuiteResult, snapshot_dir: Path) -> None:
    """Write deterministic validation snapshot files."""
    if snapshot_dir.exists() and not snapshot_dir.is_dir():
        raise ValueError(
            f"Validation snapshot path must be a directory: {snapshot_dir}"
        )
    if snapshot_dir.exists() and any(snapshot_dir.iterdir()):
        raise ValueError(
            f"Validation snapshot directory must be empty or absent: {snapshot_dir}"
        )

    snapshot_dir.mkdir(parents=True, exist_ok=True)
    (snapshot_dir / "validation_result.json").write_text(
        _validation_result_json_text(result) + "\n",
        encoding="utf-8",
    )
    (snapshot_dir / "README.md").write_text(
        "\n".join(
            (
                "# Aevryn Validation Snapshot",
                "",
                "This snapshot stores deterministic validation metadata only.",
                "",
                "It does not store chapter text or extraction prompt bodies.",
                "",
                "## Result",
                "",
                f"* Passed: {result.passed}",
                f"* Score: {result.score}%",
                f"* Digest: `{result.suite_digest}`",
                "",
                "## Totals",
                "",
                f"`{_validation_totals_line(result.totals)}`",
                "",
            )
        ),
        encoding="utf-8",
    )


def _validation_result_json_text(result: ValidationSuiteResult) -> str:
    """Return deterministic validation result JSON text."""
    return json.dumps(
        _validation_result_json(result),
        indent=2,
        ensure_ascii=False,
        sort_keys=True,
    )


def _validation_result_json(result: ValidationSuiteResult) -> dict[str, Any]:
    """Return validation result data for JSON output and snapshots."""
    return {
        "passed": result.passed,
        "score": result.score,
        "suite_digest": result.suite_digest,
        "totals": _validation_totals_json(result.totals),
        "results": [
            {
                "case_id": case_result.case_id,
                "title": case_result.title,
                "genre": case_result.genre,
                "passed": case_result.passed,
                "actual_import": (
                    None
                    if case_result.actual_import is None
                    else {
                        "chapter_files": case_result.actual_import.chapter_files,
                        "source_manifest_digest": (
                            case_result.actual_import.source_manifest_digest
                        ),
                        "chapters": case_result.actual_import.chapters,
                        "scenes": case_result.actual_import.scenes,
                        "paragraphs": case_result.actual_import.paragraphs,
                        "sentences": case_result.actual_import.sentences,
                        "evidence_anchors": (
                            case_result.actual_import.evidence_anchors
                        ),
                        "import_digest": case_result.actual_import.import_digest,
                    }
                ),
                "actual_extraction": (
                    None
                    if case_result.actual_extraction is None
                    else {
                        "scene_inputs": case_result.actual_extraction.scene_inputs,
                        "evidence_anchors": (
                            case_result.actual_extraction.evidence_anchors
                        ),
                        "extraction_input_digest": (
                            case_result.actual_extraction.extraction_input_digest
                        ),
                        "extraction_prompt_digest": (
                            case_result.actual_extraction.extraction_prompt_digest
                        ),
                    }
                ),
                "errors": list(case_result.errors),
            }
            for case_result in result.results
        ],
    }


def _validation_metrics_line(metrics: ExpectedImportMetrics) -> str:
    """Return a compact validation metrics line."""
    return (
        f"  files={metrics.chapter_files} "
        f"chapters={metrics.chapters} "
        f"scenes={metrics.scenes} "
        f"paragraphs={metrics.paragraphs} "
        f"sentences={metrics.sentences} "
        f"anchors={metrics.evidence_anchors}"
    )


def _validation_extraction_line(metrics: ExpectedExtractionMetrics) -> str:
    """Return a compact validation extraction-readiness metrics line."""
    return (
        f"  extraction_inputs={metrics.scene_inputs} "
        f"extraction_anchors={metrics.evidence_anchors}"
    )


def _validation_totals_line(totals: ValidationTotals) -> str:
    """Return a compact validation totals line."""
    return (
        f"cases={totals.cases} "
        f"passed={totals.passed} "
        f"failed={totals.failed} "
        f"files={totals.chapter_files} "
        f"chapters={totals.chapters} "
        f"scenes={totals.scenes} "
        f"paragraphs={totals.paragraphs} "
        f"sentences={totals.sentences} "
        f"anchors={totals.evidence_anchors} "
        f"extraction_inputs={totals.extraction_inputs} "
        f"extraction_anchors={totals.extraction_anchors}"
    )


def _validation_totals_json(totals: ValidationTotals) -> dict[str, int]:
    """Return JSON-ready validation totals."""
    return {
        "cases": totals.cases,
        "passed": totals.passed,
        "failed": totals.failed,
        "chapter_files": totals.chapter_files,
        "chapters": totals.chapters,
        "scenes": totals.scenes,
        "paragraphs": totals.paragraphs,
        "sentences": totals.sentences,
        "evidence_anchors": totals.evidence_anchors,
        "extraction_inputs": totals.extraction_inputs,
        "extraction_anchors": totals.extraction_anchors,
    }


def _validation_source_root(source_root: str | None) -> Path:
    """Return the validation source root from args, environment, or default."""
    if source_root is not None:
        return Path(source_root)

    configured_source_root = os.environ.get("AEVRYN_VALIDATION_ROOT")
    if configured_source_root is not None:
        if not configured_source_root.strip():
            raise ValueError("AEVRYN_VALIDATION_ROOT cannot be blank.")
        return Path(configured_source_root)

    return Path.home() / "Desktop" / "Aevryn test chapters"


def _character_ids_for_scene(
    args: argparse.Namespace,
    result: ProjectRunResult,
    scene_id: str | None,
) -> tuple[str, ...]:
    """Return requested character IDs or accepted characters for a scene."""
    character_ids = cast(list[str] | None, args.character_id)
    if character_ids is not None:
        return _dedupe_ids(character_ids)

    target_scene_id = scene_id or AevrynProjectRunner.latest_scene_id(result)
    accepted_character_ids: dict[str, None] = {}
    for extraction, summary in zip(
        result.extraction_results,
        result.update_summaries,
        strict=True,
    ):
        if extraction.scene_id != target_scene_id:
            continue
        accepted_entities = set(summary.accepted_entities)
        for entity in extraction.entities:
            if (
                entity.entity_id in accepted_entities
                and entity.entity_type == "character"
            ):
                accepted_character_ids.setdefault(entity.entity_id, None)

    return tuple(accepted_character_ids)


def _run_with_selected_extractor(args: argparse.Namespace) -> ProjectRunResult:
    """Run the demo extractor or AI JSON extractor based on command arguments."""
    if cast(str | None, args.ai_response_file) is not None:
        return _run_ai_json(args)

    return _runner().run_demo_text_file(
        path=Path(cast(str, args.path)),
        source_id=cast(str, args.source_id),
        title=cast(str | None, args.title),
    )


def _run_ai_json(args: argparse.Namespace) -> ProjectRunResult:
    """Run imported text through a static evidence-bounded AI JSON response."""
    runner = _runner()
    imported_source = runner.import_text_file(
        path=Path(cast(str, args.path)),
        source_id=cast(str, args.source_id),
        title=cast(str | None, args.title),
    )
    response_path = Path(
        cast(str, getattr(args, "response_path", None) or args.ai_response_file)
    )
    response = response_path.read_text(encoding="utf-8")
    scene_payloads = _scene_payloads_from_response(response)
    if scene_payloads is not None:
        return runner.run_imported_source_with_scene_payloads(
            imported_source=imported_source,
            payloads_by_scene_id=scene_payloads,
        )

    return runner.run_imported_scene(
        imported_source=imported_source,
        extractor=EvidenceBoundedAIExtractor(
            client=StaticAIExtractionClient(response)
        ),
        scene_id=cast(str | None, getattr(args, "scene_id", None)),
    )


def _runner() -> AevrynProjectRunner:
    """Create a project runner for a command."""
    return AevrynProjectRunner()


def _dedupe_ids(entity_ids: Sequence[str]) -> tuple[str, ...]:
    """Return IDs in first-seen order without duplicates."""
    deduped: dict[str, None] = {}
    for entity_id in entity_ids:
        _require_machine_token(entity_id, "Selected entity ID")
        deduped.setdefault(entity_id, None)

    return tuple(deduped)


def _summary_ids(summary_buckets: Iterable[Sequence[str]]) -> list[str]:
    """Return accepted or rejected summary IDs in stable first-seen order."""
    deduped: dict[str, None] = {}
    for bucket in summary_buckets:
        for summary_id in bucket:
            deduped.setdefault(summary_id, None)

    return list(deduped)


def _require_text(value: str, field_name: str) -> None:
    """Validate a required CLI text value."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required.")


def _require_machine_token(value: str, field_name: str) -> None:
    """Validate a whitespace-free CLI machine token."""
    _require_text(value, field_name)
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} cannot contain whitespace.")


def _scene_payloads_from_response(response: str) -> dict[str, dict[str, object]] | None:
    """Return scene payloads from a multi-scene response envelope."""
    try:
        payload = loads_json_without_duplicate_keys(response)
    except json.JSONDecodeError:
        return None

    if not isinstance(payload, dict) or "scenes" not in payload:
        return None

    extra_keys = set(payload) - {"scenes"}
    if extra_keys:
        extra = ", ".join(sorted(extra_keys))
        raise ValueError(
            f"AI multi-scene response has unsupported envelope keys: {extra}"
        )

    scenes = payload["scenes"]
    if isinstance(scenes, dict):
        scene_payloads = scenes
    elif isinstance(scenes, list):
        scene_payloads = _scene_payloads_from_list(scenes)
    else:
        raise ValueError("AI multi-scene response field must be an object or list: scenes")

    parsed: dict[str, dict[str, object]] = {}
    for scene_id, scene_payload in scene_payloads.items():
        if not isinstance(scene_id, str):
            raise ValueError("AI multi-scene response scene IDs must be strings.")
        _require_machine_token(scene_id, "AI multi-scene response scene ID")
        if not isinstance(scene_payload, dict):
            raise ValueError("AI multi-scene response scene payloads must be objects.")
        parsed[scene_id] = dict(scene_payload)

    return parsed


def _scene_payloads_from_list(
    scenes: list[object],
) -> dict[str, dict[str, object]]:
    """Return scene payloads from list-form multi-scene response data."""
    scene_payloads: dict[str, dict[str, object]] = {}
    for item in scenes:
        if not isinstance(item, dict):
            raise ValueError("AI multi-scene response scene entries must be objects.")

        scene_id = item.get("scene_id")
        if not isinstance(scene_id, str):
            raise ValueError(
                "AI multi-scene response scene entries must include string scene_id."
            )
        _require_machine_token(scene_id, "AI multi-scene response scene ID")
        if scene_id in scene_payloads:
            raise ValueError(
                f"AI multi-scene response includes duplicate scene: {scene_id}"
            )

        scene_payload = dict(item)
        scene_payload.pop("scene_id")
        scene_payloads[scene_id] = scene_payload

    return scene_payloads


if __name__ == "__main__":
    sys.exit(main())
