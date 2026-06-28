"""Tests for the Aevryn V2 Backend API contract."""

from __future__ import annotations

import base64
import json
import logging
from pathlib import Path
from typing import Any

from _pytest.logging import LogCaptureFixture
from fastapi.testclient import TestClient

from aevryn.api import (
    AUTH_STORE_PATH_ENV,
    EXTRACTION_MODE_ENV,
    OPENAI_API_KEY_ENV,
    OPENAI_MAX_RESPONSE_BYTES_ENV,
    OPENAI_MODEL_ENV,
    OPENAI_TIMEOUT_SECONDS_ENV,
    PROJECT_DATABASE_PATH_ENV,
    create_app,
    create_app_from_env,
)
from aevryn.api.app import _worker_extractor_from_env
from aevryn.extraction import EvidenceBoundedAIExtractor
from aevryn.import_storage import InMemoryImportContentStore
from aevryn.persistence import InMemoryProjectRepository


def test_health_endpoint_reports_api_status() -> None:
    """Health endpoint should not require engine state."""
    client = TestClient(create_app())

    response = client.get("/v2/health")

    assert response.status_code == 200
    assert response.json() == {
        "api_version": "v2",
        "engine": "Aevryn",
        "storage": {
            "project_storage": "unconfigured",
            "import_content_storage": "unconfigured",
        },
        "status": "ok",
    }


def test_health_endpoint_reports_configured_storage() -> None:
    """Health endpoint should report storage adapter availability without reading data."""
    client = TestClient(
        create_app(
            project_repository=InMemoryProjectRepository(),
            import_content_store=InMemoryImportContentStore(),
        )
    )

    response = client.get("/v2/health")

    assert response.status_code == 200
    assert response.json()["storage"] == {
        "project_storage": "configured",
        "import_content_storage": "configured",
    }


def test_api_responses_include_identity_headers() -> None:
    """API responses should include stable identity headers."""
    client = TestClient(create_app())

    response = client.get("/v2")

    assert response.status_code == 200
    assert response.headers["x-Aevryn-api-version"] == "v2"
    assert response.headers["x-Aevryn-engine"] == "Aevryn"
    assert response.headers["x-request-id"]


def test_api_error_responses_include_identity_headers() -> None:
    """API errors should include the same identity headers as success responses."""
    client = TestClient(create_app())

    response = client.get("/v2/missing")

    assert response.status_code == 404
    assert response.headers["x-Aevryn-api-version"] == "v2"
    assert response.headers["x-Aevryn-engine"] == "Aevryn"
    assert response.headers["x-request-id"]
    assert response.json()["error"] == "request_failed"


def test_api_echoes_client_request_id() -> None:
    """API should echo a valid client request ID for trace correlation."""
    client = TestClient(create_app())

    response = client.get("/v2", headers={"X-Request-ID": "demo-request-123"})

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "demo-request-123"


def test_api_generates_request_id_when_client_value_is_invalid() -> None:
    """API should not echo whitespace-bearing request IDs."""
    client = TestClient(create_app())

    response = client.get("/v2", headers={"X-Request-ID": "bad request id"})

    assert response.status_code == 200
    assert response.headers["x-request-id"] != "bad request id"
    assert response.headers["x-request-id"]


def test_cors_is_disabled_by_default() -> None:
    """API app should not allow browser origins unless configured."""
    client = TestClient(create_app())

    response = client.options(
        "/v2/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 405
    assert "access-control-allow-origin" not in response.headers


def test_create_app_can_enable_configured_cors_origin() -> None:
    """API app should allow explicitly configured browser origins."""
    client = TestClient(create_app(allowed_origins=("http://localhost:5173",)))

    response = client.options(
        "/v2/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "GET" in response.headers["access-control-allow-methods"]

    delete_response = client.options(
        "/v2/projects/project_alpha/stories/story_alpha",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "DELETE",
        },
    )

    assert delete_response.status_code == 200
    assert delete_response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "DELETE" in delete_response.headers["access-control-allow-methods"]


def test_create_app_from_env_configures_cors_origins() -> None:
    """Environment app factory should configure explicit browser origins."""
    client = TestClient(
        create_app_from_env(
            {
                "AEVRYN_API_ALLOWED_ORIGINS": (
                    "http://localhost:5173, https://app.aevryn.local"
                )
            }
        )
    )

    response = client.options(
        "/v2/health",
        headers={
            "Origin": "https://app.aevryn.local",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == (
        "https://app.aevryn.local"
    )


def test_create_app_from_env_configures_project_storage(
    tmp_path: Path,
) -> None:
    """Environment app factory should wire durable local project storage."""
    database_path = tmp_path / "project_database.json"
    auth_store_path = tmp_path / "auth_store.json"
    environ = {
        PROJECT_DATABASE_PATH_ENV: str(database_path),
        AUTH_STORE_PATH_ENV: str(auth_store_path),
    }
    client = TestClient(create_app_from_env(environ))
    now = "2026-06-27T00:00:00Z"

    register = client.post(
        "/v2/auth/register",
        json={
            "user_id": "user_demo",
            "email": "demo@example.com",
            "display_name": "Demo User",
            "password": "StrongPass123",
            "now": now,
        },
    )
    assert register.status_code == 200
    session_token = register.json()["session_token"]
    headers = {
        "Authorization": f"Bearer {session_token}",
        "X-Aevryn-Now": now,
    }

    created = client.post(
        "/v2/projects",
        json={"project_id": "project_demo", "name": " Demo   Novel ", "now": now},
        headers=headers,
    )
    assert created.status_code == 200
    assert created.json() == {
        "project_id": "project_demo",
        "name": "Demo Novel",
        "created_at": now,
        "updated_at": now,
    }

    listed = client.get("/v2/projects", headers=headers)
    assert listed.status_code == 200
    assert listed.json()["projects"] == [created.json()]
    assert database_path.exists()
    assert auth_store_path.exists()

    reloaded_client = TestClient(create_app_from_env(environ))
    login = reloaded_client.post(
        "/v2/auth/login",
        json={"email": "demo@example.com", "password": "StrongPass123", "now": now},
    )
    assert login.status_code == 200
    reloaded_headers = {
        "Authorization": f"Bearer {login.json()['session_token']}",
        "X-Aevryn-Now": now,
    }
    reloaded_listed = reloaded_client.get("/v2/projects", headers=reloaded_headers)
    assert reloaded_listed.status_code == 200
    assert reloaded_listed.json()["projects"] == [created.json()]

    default_database_path = tmp_path / "default_project_database.json"
    default_client = TestClient(
        create_app_from_env({PROJECT_DATABASE_PATH_ENV: str(default_database_path)})
    )
    default_register = default_client.post(
        "/v2/auth/register",
        json={
            "user_id": "user_default",
            "email": "default@example.com",
            "display_name": "Default User",
            "password": "StrongPass123",
            "now": now,
        },
    )
    assert default_register.status_code == 200
    assert (tmp_path / "default_project_database_auth.json").exists()


def test_create_app_from_env_rejects_wildcard_cors_origin() -> None:
    """Environment app factory should not allow broad CORS by accident."""
    try:
        create_app_from_env({"AEVRYN_API_ALLOWED_ORIGINS": "*"})
    except ValueError as error:
        assert "cannot include '*'" in str(error)
    else:
        raise AssertionError("Expected wildcard CORS origin to be rejected.")


def test_api_key_auth_keeps_discovery_routes_public() -> None:
    """Configured API keys should not block public discovery metadata."""
    client = TestClient(create_app(api_keys=("secret-key",)))

    response = client.get("/v2/capabilities")

    assert response.status_code == 200
    assert response.json()["engine"] == "Aevryn"


def test_api_key_auth_rejects_missing_key_for_workflow_routes() -> None:
    """Configured API keys should protect every Phase 1 workflow route."""
    client = TestClient(create_app(api_keys=("secret-key",)))

    workflow_routes = (
        "/v2/imports/inspect",
        "/v2/extraction-prompts",
        "/v2/extractions/apply",
        "/v2/canon/preview",
        "/v2/timeline/preview",
        "/v2/projects/preview",
        "/v2/characters/preview",
        "/v2/scenes/preview",
        "/v2/prompts/preview",
        "/v2/world/preview",
        "/v2/continuity/preview",
        "/v2/project-outputs/preview",
        "/v2/exports/preview",
    )

    for route in workflow_routes:
        response = client.post(route, json={})

        assert response.status_code == 401, route
        assert response.headers["x-Aevryn-api-version"] == "v2"
        assert response.json() == {
            "detail": "A valid API key is required for this workflow route.",
            "error": "authentication_required",
        }


def test_api_key_auth_rejects_invalid_key_for_workflow_routes() -> None:
    """Configured API keys should reject incorrect workflow credentials."""
    client = TestClient(create_app(api_keys=("secret-key",)))

    response = client.post(
        "/v2/imports/inspect",
        headers={"X-Aevryn-API-Key": "wrong-key"},
        json={
            "source_id": "api_demo",
            "filename": "chapter.txt",
            "content_base64": _b64("Chapter 1\nMark carried a rusty dagger."),
        },
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "The provided API key is not authorized.",
        "error": "invalid_api_key",
    }


def test_api_key_auth_accepts_explicit_header_for_workflow_routes() -> None:
    """Configured API keys should allow workflow routes with the API-key header."""
    client = TestClient(create_app(api_keys=("secret-key",)))

    response = client.post(
        "/v2/imports/inspect",
        headers={"X-Aevryn-API-Key": "secret-key"},
        json={
            "source_id": "api_demo",
            "filename": "chapter.txt",
            "content_base64": _b64("Chapter 1\nMark carried a rusty dagger."),
        },
    )

    assert response.status_code == 200
    assert response.json()["source_id"] == "api_demo"


def test_api_key_auth_accepts_bearer_header_for_workflow_routes() -> None:
    """Configured API keys should allow standard Bearer credentials."""
    client = TestClient(create_app(api_keys=("secret-key",)))

    response = client.post(
        "/v2/imports/inspect",
        headers={"Authorization": "Bearer secret-key"},
        json={
            "source_id": "api_demo",
            "filename": "chapter.txt",
            "content_base64": _b64("Chapter 1\nMark carried a rusty dagger."),
        },
    )

    assert response.status_code == 200
    assert response.json()["source_id"] == "api_demo"


def test_create_app_from_env_configures_api_keys() -> None:
    """Environment app factory should configure workflow API keys."""
    client = TestClient(create_app_from_env({"AEVRYN_API_KEYS": "secret-key"}))

    response = client.post(
        "/v2/imports/inspect",
        headers={"X-Aevryn-API-Key": "secret-key"},
        json={
            "source_id": "api_demo",
            "filename": "chapter.txt",
            "content_base64": _b64("Chapter 1\nMark carried a rusty dagger."),
        },
    )

    assert response.status_code == 200


def test_worker_extractor_env_defaults_to_demo_mode() -> None:
    """Provider-backed extraction should not be enabled implicitly."""
    assert _worker_extractor_from_env({}) is None
    assert _worker_extractor_from_env({EXTRACTION_MODE_ENV: "demo"}) is None


def test_worker_extractor_env_configures_openai_mode() -> None:
    """OpenAI extraction should require explicit mode, key, and model."""
    extractor = _worker_extractor_from_env(
        {
            EXTRACTION_MODE_ENV: "openai",
            OPENAI_API_KEY_ENV: "test-key",
            OPENAI_MODEL_ENV: "test-model",
            OPENAI_TIMEOUT_SECONDS_ENV: "12.5",
            OPENAI_MAX_RESPONSE_BYTES_ENV: "2048",
        }
    )

    assert isinstance(extractor, EvidenceBoundedAIExtractor)


def test_worker_extractor_env_rejects_incomplete_openai_mode() -> None:
    """OpenAI extraction config should fail before any worker can process text."""
    try:
        _worker_extractor_from_env({EXTRACTION_MODE_ENV: "openai"})
    except ValueError as error:
        assert OPENAI_API_KEY_ENV in str(error)
    else:
        raise AssertionError("Expected missing OpenAI API key to be rejected.")

    try:
        _worker_extractor_from_env(
            {
                EXTRACTION_MODE_ENV: "openai",
                OPENAI_API_KEY_ENV: "test-key",
            }
        )
    except ValueError as error:
        assert OPENAI_MODEL_ENV in str(error)
    else:
        raise AssertionError("Expected missing OpenAI model to be rejected.")


def test_worker_extractor_env_rejects_invalid_values() -> None:
    """Extraction mode and numeric provider settings should fail clearly."""
    for environ, expected in (
        ({EXTRACTION_MODE_ENV: "magic"}, EXTRACTION_MODE_ENV),
        (
            {
                EXTRACTION_MODE_ENV: "openai",
                OPENAI_API_KEY_ENV: "test-key",
                OPENAI_MODEL_ENV: "test-model",
                OPENAI_TIMEOUT_SECONDS_ENV: "0",
            },
            OPENAI_TIMEOUT_SECONDS_ENV,
        ),
        (
            {
                EXTRACTION_MODE_ENV: "openai",
                OPENAI_API_KEY_ENV: "test-key",
                OPENAI_MODEL_ENV: "test-model",
                OPENAI_MAX_RESPONSE_BYTES_ENV: "-1",
            },
            OPENAI_MAX_RESPONSE_BYTES_ENV,
        ),
    ):
        try:
            _worker_extractor_from_env(environ)
        except ValueError as error:
            assert expected in str(error)
        else:
            raise AssertionError(f"Expected invalid extraction config: {expected}")


def test_create_app_from_env_accepts_explicit_openai_extraction_mode(
    tmp_path: Path,
) -> None:
    """App env wiring should build the worker handler without calling providers."""
    client = TestClient(
        create_app_from_env(
            {
                PROJECT_DATABASE_PATH_ENV: str(tmp_path / "project_database.json"),
                EXTRACTION_MODE_ENV: "openai",
                OPENAI_API_KEY_ENV: "test-key",
                OPENAI_MODEL_ENV: "test-model",
            }
        )
    )

    response = client.get("/v2/health")

    assert response.status_code == 200


def test_create_app_rejects_duplicate_api_keys() -> None:
    """API-key configuration should reject ambiguous duplicate keys."""
    try:
        create_app(api_keys=("secret-key", " secret-key "))
    except ValueError as error:
        assert "duplicate keys" in str(error)
    else:
        raise AssertionError("Expected duplicate API keys to be rejected.")


def test_api_index_reports_entrypoint_links() -> None:
    """Version index should expose the main API entry points."""
    client = TestClient(create_app())

    response = client.get("/v2")

    assert response.status_code == 200
    payload = response.json()
    links = {link["rel"]: link for link in payload["links"]}
    assert payload["api_version"] == "v2"
    assert payload["phase"] == "v2_phase_1_backend_api"
    assert links["health"] == {
        "href": "/v2/health",
        "method": "GET",
        "rel": "health",
    }
    assert links["capabilities"]["href"] == "/v2/capabilities"
    assert links["openapi"]["href"] == "/openapi.json"
    assert "No production Project Database configured yet." in payload["platform_limits"]


def test_source_formats_endpoint_reports_supported_and_deferred_formats() -> None:
    """Source format metadata should match V1.1 import policy."""
    client = TestClient(create_app())

    response = client.get("/v2/source-formats")

    assert response.status_code == 200
    payload = response.json()
    supported_extensions = {
        item["extension"] for item in payload["supported"]
    }
    deferred_extensions = {
        item["extension"] for item in payload["deferred"]
    }
    assert ".txt" in supported_extensions
    assert ".epub" in supported_extensions
    assert ".pdf" in deferred_extensions
    assert ".mobi" in deferred_extensions
    assert ".azw3" in deferred_extensions


def test_capabilities_endpoint_reports_routes_and_limits() -> None:
    """Capabilities endpoint should expose frontend-discoverable API metadata."""
    client = TestClient(create_app())

    response = client.get("/v2/capabilities")

    assert response.status_code == 200
    payload = response.json()
    route_paths = {route["path"] for route in payload["routes"]}
    export_capabilities = {
        item["export_kind"]: item["formats"]
        for item in payload["export_capabilities"]
    }
    assert payload["api_version"] == "v2"
    assert payload["phase"] == "v2_phase_1_backend_api"
    assert "/v2" in route_paths
    assert "/v2/canon/preview" in route_paths
    assert "/v2/timeline/preview" in route_paths
    assert "/v2/projects/preview" in route_paths
    assert "/v2/projects/{project_id}/status" in route_paths
    assert "/v2/projects/{project_id}/outputs" in route_paths
    assert "/v2/characters/preview" in route_paths
    assert "/v2/scenes/preview" in route_paths
    assert "/v2/prompts/preview" in route_paths
    assert "/v2/world/preview" in route_paths
    assert "/v2/continuity/preview" in route_paths
    assert "/v2/project-outputs/preview" in route_paths
    assert "/v2/exports/preview" in route_paths
    assert ".epub" in {
        item["extension"] for item in payload["source_formats"]["supported"]
    }
    assert export_capabilities["prompt_bundle"] == ["markdown", "json", "csv"]
    assert "No production Project Database configured yet." in payload["platform_limits"]


def test_openapi_schema_uses_stable_operation_ids_and_tags() -> None:
    """OpenAPI schema should be stable enough for frontend tooling."""
    client = TestClient(create_app())

    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert paths["/v2"]["get"]["operationId"] == "getV2Index"
    assert paths["/v2"]["get"]["tags"] == ["System"]
    assert paths["/v2/health"]["get"]["operationId"] == "getV2Health"
    assert paths["/v2/health"]["get"]["tags"] == ["System"]
    assert paths["/v2/capabilities"]["get"]["operationId"] == (
        "getV2Capabilities"
    )
    assert paths["/v2/capabilities"]["get"]["tags"] == ["System"]
    assert paths["/v2/source-formats"]["get"]["operationId"] == (
        "getV2SourceFormats"
    )
    assert paths["/v2/source-formats"]["get"]["tags"] == ["Import"]
    assert paths["/v2/projects/{project_id}/status"]["get"]["operationId"] == (
        "getV2ProjectStatus"
    )
    assert paths["/v2/projects/{project_id}/status"]["get"]["tags"] == ["Projects"]
    assert paths["/v2/projects/{project_id}/outputs"]["get"]["operationId"] == (
        "getV2ProjectOutputs"
    )
    assert paths["/v2/projects/{project_id}/outputs"]["get"]["tags"] == ["Projects"]
    assert paths["/v2/imports/inspect"]["post"]["operationId"] == (
        "postV2ImportsInspect"
    )
    assert paths["/v2/imports/inspect"]["post"]["tags"] == ["Import"]
    assert paths["/v2/extraction-prompts"]["post"]["operationId"] == (
        "postV2ExtractionPrompts"
    )
    assert paths["/v2/extraction-prompts"]["post"]["tags"] == ["Extraction"]
    assert paths["/v2/extractions/apply"]["post"]["operationId"] == (
        "postV2ExtractionsApply"
    )
    assert paths["/v2/extractions/apply"]["post"]["tags"] == ["Extraction"]
    assert paths["/v2/canon/preview"]["post"]["operationId"] == (
        "postV2CanonPreview"
    )
    assert paths["/v2/canon/preview"]["post"]["tags"] == ["Canon"]
    assert paths["/v2/timeline/preview"]["post"]["operationId"] == (
        "postV2TimelinePreview"
    )
    assert paths["/v2/timeline/preview"]["post"]["tags"] == ["Timeline"]
    assert paths["/v2/projects/preview"]["post"]["operationId"] == (
        "postV2ProjectsPreview"
    )
    assert paths["/v2/projects/preview"]["post"]["tags"] == ["Projects"]
    assert paths["/v2/characters/preview"]["post"]["operationId"] == (
        "postV2CharactersPreview"
    )
    assert paths["/v2/characters/preview"]["post"]["tags"] == ["Characters"]
    assert paths["/v2/scenes/preview"]["post"]["operationId"] == (
        "postV2ScenesPreview"
    )
    assert paths["/v2/scenes/preview"]["post"]["tags"] == ["Scenes"]
    assert paths["/v2/prompts/preview"]["post"]["operationId"] == (
        "postV2PromptsPreview"
    )
    assert paths["/v2/prompts/preview"]["post"]["tags"] == ["Prompts"]
    assert paths["/v2/world/preview"]["post"]["operationId"] == (
        "postV2WorldPreview"
    )
    assert paths["/v2/world/preview"]["post"]["tags"] == ["World"]
    assert paths["/v2/continuity/preview"]["post"]["operationId"] == (
        "postV2ContinuityPreview"
    )
    assert paths["/v2/continuity/preview"]["post"]["tags"] == ["Continuity"]
    assert paths["/v2/project-outputs/preview"]["post"]["operationId"] == (
        "postV2ProjectOutputsPreview"
    )
    assert paths["/v2/project-outputs/preview"]["post"]["tags"] == [
        "Project Outputs"
    ]
    assert paths["/v2/exports/preview"]["post"]["operationId"] == (
        "postV2ExportsPreview"
    )
    assert paths["/v2/exports/preview"]["post"]["tags"] == ["Exports"]


def test_import_inspect_endpoint_uses_engine_import_without_source_text_leak() -> None:
    """Import API should expose structure metadata without returning story text."""
    client = TestClient(create_app())

    response = client.post(
        "/v2/imports/inspect",
        json={
            "source_id": "api_demo",
            "filename": "chapter.txt",
            "title": "API Demo",
            "content_base64": _b64(
                "Chapter 1\nMark carried a rusty dagger.\n\n"
                "Chapter 2\nMark bought an iron sword."
            ),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_id"] == "api_demo"
    assert payload["source_format"] == "txt"
    assert payload["title"] == "API Demo"
    assert payload["chapters"] == 2
    assert payload["chapter_ids"] == [
        "api_demo_chapter_001",
        "api_demo_chapter_002",
    ]
    assert payload["scenes"] == 2
    assert payload["evidence_anchors"] == 2
    assert "Mark carried a rusty dagger." not in response.text
    assert "quote" not in payload["first_evidence_anchors"][0]


def test_import_inspect_logs_duration_without_source_payload(
    caplog: LogCaptureFixture,
) -> None:
    """Import inspect timing logs should stay metadata-only."""
    client = TestClient(create_app())

    with caplog.at_level(logging.INFO, logger="aevryn.api.app"):
        response = client.post(
            "/v2/imports/inspect",
            json={
                "source_id": "api_demo",
                "filename": "chapter.txt",
                "content_base64": _b64("Chapter 1\nMark carried a rusty dagger."),
            },
        )

    assert response.status_code == 200
    record = _workflow_log_record(caplog, "import_inspect", "succeeded")
    _assert_duration_log(record)
    assert getattr(record, "scene_count", 0) == 1
    assert getattr(record, "evidence_anchor_count", 0) == 1
    assert "Mark carried a rusty dagger" not in _caplog_record_text(caplog)


def test_import_inspect_endpoint_rejects_invalid_base64() -> None:
    """Import API should fail clearly for malformed content payloads."""
    client = TestClient(create_app())

    response = client.post(
        "/v2/imports/inspect",
        json={
            "source_id": "api_demo",
            "filename": "chapter.txt",
            "content_base64": "not base64",
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "content_base64 is invalid.",
        "error": "invalid_base64",
    }


def test_import_inspect_endpoint_rejects_deferred_source_format() -> None:
    """Import API should not claim unsupported parser formats."""
    client = TestClient(create_app())

    response = client.post(
        "/v2/imports/inspect",
        json={
            "source_id": "api_demo",
            "filename": "chapter.pdf",
            "content_base64": _b64("placeholder"),
        },
    )

    assert response.status_code == 400
    assert response.json()["error"] == "import_failed"
    assert "requires a dedicated parser dependency" in response.json()["detail"]


def test_import_inspect_endpoint_returns_stable_validation_error() -> None:
    """Import API should return stable 422 error shape for malformed requests."""
    client = TestClient(create_app())

    response = client.post(
        "/v2/imports/inspect",
        json={
            "filename": "chapter.txt",
            "content_base64": _b64("Chapter 1\nMark carried a rusty dagger."),
        },
    )

    assert response.status_code == 422
    assert response.json()["error"] == "invalid_request"
    assert "source_id" in response.json()["detail"]


def test_extraction_prompt_endpoint_builds_prompt_for_first_scene() -> None:
    """Extraction prompt API should use the same evidence-bounded engine prompt."""
    client = TestClient(create_app())

    response = client.post(
        "/v2/extraction-prompts",
        json={
            "source_id": "api_demo",
            "filename": "chapter.txt",
            "title": "API Demo",
            "content_base64": _b64("Chapter 1\nMark carried a rusty dagger."),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_id"] == "api_demo"
    assert payload["source_format"] == "txt"
    assert payload["scene_id"] == "api_demo_chapter_001_scene_001"
    assert payload["evidence_anchor_count"] == 1
    assert "Use only the provided evidence anchors." in payload["prompt"]
    assert "api_demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor" in (
        payload["prompt"]
    )


def test_extraction_prompt_endpoint_can_select_scene() -> None:
    """Extraction prompt API should support explicit scene selection."""
    client = TestClient(create_app())

    response = client.post(
        "/v2/extraction-prompts",
        json={
            "source_id": "api_demo",
            "filename": "chapter.txt",
            "content_base64": _b64(
                "Chapter 1\nMark carried a rusty dagger.\n\n"
                "Chapter 2\nMark bought an iron sword."
            ),
            "scene_id": "api_demo_chapter_002_scene_001",
        },
    )

    assert response.status_code == 200
    assert response.json()["scene_id"] == "api_demo_chapter_002_scene_001"
    assert "Mark bought an iron sword." in response.json()["prompt"]


def test_extraction_prompt_endpoint_rejects_unknown_scene() -> None:
    """Extraction prompt API should return a stable error for unknown scenes."""
    client = TestClient(create_app())

    response = client.post(
        "/v2/extraction-prompts",
        json={
            "source_id": "api_demo",
            "filename": "chapter.txt",
            "content_base64": _b64("Chapter 1\nMark carried a rusty dagger."),
            "scene_id": "api_demo_chapter_999_scene_001",
        },
    )

    assert response.status_code == 400
    assert response.json()["error"] == "extraction_prompt_failed"
    assert "Unknown scene" in response.json()["detail"]


def test_extractions_apply_endpoint_accepts_single_scene_payload() -> None:
    """Extraction apply API should pass candidates through Canon Updating."""
    client = TestClient(create_app())
    anchor_id = "api_demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor"

    response = client.post(
        "/v2/extractions/apply",
        json={
            "source_id": "api_demo",
            "filename": "chapter.txt",
            "content_base64": _b64("Chapter 1\nMark carried a rusty dagger."),
            "ai_response": weapon_payload(anchor_id=anchor_id, weapon="Rusty Dagger"),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["results"] == [
        {
            "entities": 1,
            "facts": 1,
            "relationships": 0,
            "scene_id": "api_demo_chapter_001_scene_001",
            "state_changes": 0,
        }
    ]
    assert payload["accepted_entity_ids"] == ["character_mark"]
    assert "fact_character_mark_current_weapon_rusty_dagger" in (
        payload["accepted_fact_ids"]
    )
    assert payload["rejected_candidate_ids"] == []


def test_extraction_apply_logs_metadata_only_workflow_event(
    caplog: LogCaptureFixture,
) -> None:
    """Extraction apply should be observable without logging source or AI payloads."""
    client = TestClient(create_app())
    anchor_id = "api_demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor"

    with caplog.at_level(logging.INFO, logger="aevryn.api.app"):
        response = client.post(
            "/v2/extractions/apply",
            json={
                "source_id": "api_demo",
                "filename": "chapter.txt",
                "content_base64": _b64("Chapter 1\nMark carried a rusty dagger."),
                "ai_response": weapon_payload(anchor_id=anchor_id, weapon="Rusty Dagger"),
            },
        )

    assert response.status_code == 200
    record = _workflow_log_record(caplog, "extraction_apply", "succeeded")
    _assert_duration_log(record)
    assert getattr(record, "source_id", "") == "api_demo"
    assert getattr(record, "source_format", "") == "txt"
    assert getattr(record, "scene_count", 0) == 1
    assert getattr(record, "extraction_result_count", 0) == 1
    assert "Mark carried a rusty dagger" not in _caplog_record_text(caplog)
    assert "Rusty Dagger" not in _caplog_record_text(caplog)


def test_extractions_apply_endpoint_accepts_multi_scene_envelope() -> None:
    """Extraction apply API should support the CLI's multi-scene envelope shape."""
    client = TestClient(create_app())
    first_anchor_id = "api_demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor"
    second_anchor_id = "api_demo_chapter_002_scene_001_paragraph_001_sentence_001_anchor"

    response = client.post(
        "/v2/extractions/apply",
        json={
            "source_id": "api_demo",
            "filename": "chapter.txt",
            "content_base64": _b64(
                "Chapter 1\nMark carried a rusty dagger.\n\n"
                "Chapter 2\nMark bought an iron sword."
            ),
            "ai_response": {
                "scenes": {
                    "api_demo_chapter_001_scene_001": weapon_payload(
                        anchor_id=first_anchor_id,
                        weapon="Rusty Dagger",
                    ),
                    "api_demo_chapter_002_scene_001": weapon_payload(
                        anchor_id=second_anchor_id,
                        weapon="Iron Sword",
                    ),
                }
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert [result["scene_id"] for result in payload["results"]] == [
        "api_demo_chapter_001_scene_001",
        "api_demo_chapter_002_scene_001",
    ]
    assert payload["accepted_entities"] == 2
    assert payload["accepted_facts"] == 3
    assert "fact_character_mark_current_weapon_rusty_dagger" in (
        payload["accepted_fact_ids"]
    )
    assert "fact_character_mark_current_weapon_iron_sword" in (
        payload["accepted_fact_ids"]
    )


def test_extractions_apply_endpoint_rejects_invalid_payload() -> None:
    """Extraction apply API should report engine validation failures."""
    client = TestClient(create_app())

    response = client.post(
        "/v2/extractions/apply",
        json={
            "source_id": "api_demo",
            "filename": "chapter.txt",
            "content_base64": _b64("Chapter 1\nMark carried a rusty dagger."),
            "ai_response": {"entities": []},
        },
    )

    assert response.status_code == 400
    assert response.json()["error"] == "extraction_apply_failed"
    assert "missing required keys" in response.json()["detail"]


def test_canon_preview_returns_accepted_canon_metadata() -> None:
    """Canon API should expose accepted Canon metadata without source prose."""
    client = TestClient(create_app())
    anchor_id = "api_demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor"

    response = client.post(
        "/v2/canon/preview",
        json={
            "source_id": "api_demo",
            "filename": "chapter.txt",
            "content_base64": _b64("Chapter 1\nMark carried a rusty dagger."),
            "ai_response": weapon_payload(anchor_id=anchor_id, weapon="Rusty Dagger"),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_id"] == "api_demo"
    assert payload["source_format"] == "txt"
    assert payload["accepted_entities"] == 1
    assert payload["accepted_entity_ids"] == ["character_mark"]
    assert payload["accepted_facts"] >= 1
    assert "fact_character_mark_current_weapon_rusty_dagger" in payload[
        "accepted_fact_ids"
    ]
    assert payload["rejected_candidate_ids"] == []
    assert "Mark carried a rusty dagger." not in response.text


def test_preview_success_logs_metadata_only_workflow_event(
    caplog: LogCaptureFixture,
) -> None:
    """Preview routes should emit metadata-only success observability."""
    client = TestClient(create_app())
    anchor_id = "api_demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor"

    with caplog.at_level(logging.INFO, logger="aevryn.api.app"):
        response = client.post(
            "/v2/canon/preview",
            json={
                "source_id": "api_demo",
                "filename": "chapter.txt",
                "content_base64": _b64("Chapter 1\nMark carried a rusty dagger."),
                "ai_response": weapon_payload(anchor_id=anchor_id, weapon="Rusty Dagger"),
            },
        )

    assert response.status_code == 200
    record = _workflow_log_record(caplog, "canon_preview", "succeeded")
    _assert_duration_log(record)
    assert getattr(record, "source_id", "") == "api_demo"
    assert getattr(record, "source_format", "") == "txt"
    assert getattr(record, "scene_count", 0) == 1
    assert getattr(record, "extraction_result_count", 0) == 1
    assert "Mark carried a rusty dagger" not in _caplog_record_text(caplog)
    assert "Rusty Dagger" not in _caplog_record_text(caplog)


def test_timeline_preview_returns_scene_order_and_state_changes() -> None:
    """Timeline API should expose order and validity metadata without prose."""
    client = TestClient(create_app())
    first_anchor_id = "api_demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor"
    second_anchor_id = "api_demo_chapter_002_scene_001_paragraph_001_sentence_001_anchor"

    response = client.post(
        "/v2/timeline/preview",
        json={
            "source_id": "api_demo",
            "filename": "chapter.txt",
            "content_base64": _b64(
                "Chapter 1\nMark carried a rusty dagger.\n\n"
                "Chapter 2\nMark bought an iron sword."
            ),
            "ai_response": {
                "scenes": {
                    "api_demo_chapter_001_scene_001": weapon_payload(
                        anchor_id=first_anchor_id,
                        weapon="Rusty Dagger",
                    ),
                    "api_demo_chapter_002_scene_001": weapon_payload(
                        anchor_id=second_anchor_id,
                        weapon="Iron Sword",
                    ),
                }
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_id"] == "api_demo"
    assert payload["current_scene_id"] == "api_demo_chapter_002_scene_001"
    assert payload["chapter_ids"] == [
        "api_demo_chapter_001",
        "api_demo_chapter_002",
    ]
    assert [scene["scene_id"] for scene in payload["scene_map"]] == [
        "api_demo_chapter_001_scene_001",
        "api_demo_chapter_002_scene_001",
    ]
    assert payload["accepted_state_change_ids"]
    assert "Mark bought an iron sword." not in response.text


def test_canon_preview_rejects_invalid_payload() -> None:
    """Canon preview should report candidate application failures clearly."""
    client = TestClient(create_app())

    response = client.post(
        "/v2/canon/preview",
        json={
            "source_id": "api_demo",
            "filename": "chapter.txt",
            "content_base64": _b64("Chapter 1\nMark carried a rusty dagger."),
            "ai_response": {"entities": []},
        },
    )

    assert response.status_code == 400
    assert response.json()["error"] == "canon_preview_failed"
    assert "missing required keys" in response.json()["detail"]


def test_projects_preview_returns_stateless_project_metadata() -> None:
    """Project preview should expose project-level API metadata without storage."""
    client = TestClient(create_app())
    first_anchor_id = "api_demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor"
    second_anchor_id = "api_demo_chapter_002_scene_001_paragraph_001_sentence_001_anchor"

    response = client.post(
        "/v2/projects/preview",
        json={
            "source_id": "api_demo",
            "filename": "chapter.txt",
            "title": "API Demo",
            "content_base64": _b64(
                "Chapter 1\nMark carried a rusty dagger.\n\n"
                "Chapter 2\nMark bought an iron sword."
            ),
            "ai_response": {
                "scenes": {
                    "api_demo_chapter_001_scene_001": weapon_payload(
                        anchor_id=first_anchor_id,
                        weapon="Rusty Dagger",
                    ),
                    "api_demo_chapter_002_scene_001": weapon_payload(
                        anchor_id=second_anchor_id,
                        weapon="Iron Sword",
                    ),
                }
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    links = {link["rel"]: link for link in payload["available_outputs"]}
    assert payload["source_id"] == "api_demo"
    assert payload["source_format"] == "txt"
    assert payload["title"] == "API Demo"
    assert payload["chapter_ids"] == [
        "api_demo_chapter_001",
        "api_demo_chapter_002",
    ]
    assert payload["scene_ids"] == [
        "api_demo_chapter_001_scene_001",
        "api_demo_chapter_002_scene_001",
    ]
    assert payload["current_scene_id"] == "api_demo_chapter_002_scene_001"
    assert payload["evidence_anchors"] == 2
    assert payload["accepted_entity_ids"] == ["character_mark"]
    assert "fact_character_mark_current_weapon_iron_sword" in payload[
        "accepted_fact_ids"
    ]
    assert links["characters"]["href"] == "/v2/characters/preview"
    assert links["scene"]["href"] == "/v2/scenes/preview"
    assert links["prompts"]["href"] == "/v2/prompts/preview"
    assert links["world"]["href"] == "/v2/world/preview"
    assert links["continuity"]["href"] == "/v2/continuity/preview"
    assert links["project_outputs"]["href"] == "/v2/project-outputs/preview"
    assert links["exports"]["href"] == "/v2/exports/preview"
    assert "No production Project Database configured yet." in payload["platform_limits"]
    assert "Mark bought an iron sword." not in response.text


def test_projects_preview_rejects_invalid_payload() -> None:
    """Project preview should report candidate application failures clearly."""
    client = TestClient(create_app())

    response = client.post(
        "/v2/projects/preview",
        json={
            "source_id": "api_demo",
            "filename": "chapter.txt",
            "content_base64": _b64("Chapter 1\nMark carried a rusty dagger."),
            "ai_response": {"entities": []},
        },
    )

    assert response.status_code == 400
    assert response.json()["error"] == "project_preview_failed"
    assert "missing required keys" in response.json()["detail"]


def test_preview_failure_logs_stable_machine_code_without_payload(
    caplog: LogCaptureFixture,
) -> None:
    """Preview failures should be observable by machine code without source prose."""
    client = TestClient(create_app())

    with caplog.at_level(logging.WARNING, logger="aevryn.api.app"):
        response = client.post(
            "/v2/projects/preview",
            json={
                "source_id": "api_demo",
                "filename": "chapter.txt",
                "content_base64": _b64("Chapter 1\nMark carried a rusty dagger."),
                "ai_response": {"entities": []},
            },
        )

    assert response.status_code == 400
    record = _workflow_log_record(caplog, "project_preview", "failed")
    _assert_duration_log(record)
    assert getattr(record, "error_code", "") == "project_preview_failed"
    assert "missing required keys" in str(getattr(record, "error_summary", ""))
    assert "Mark carried a rusty dagger" not in _caplog_record_text(caplog)
    assert "entities" not in _caplog_record_text(caplog)


def test_preview_routes_return_route_specific_engine_errors() -> None:
    """Preview routes should keep stable error codes for engine failures."""
    client = TestClient(create_app())
    routes = {
        "/v2/timeline/preview": "timeline_preview_failed",
        "/v2/characters/preview": "character_preview_failed",
        "/v2/scenes/preview": "scene_preview_failed",
        "/v2/prompts/preview": "prompt_preview_failed",
        "/v2/world/preview": "world_preview_failed",
        "/v2/continuity/preview": "continuity_preview_failed",
    }

    for route, error_code in routes.items():
        response = client.post(
            route,
            json={
                "source_id": "api_demo",
                "filename": "chapter.txt",
                "content_base64": _b64("Chapter 1\nMark carried a rusty dagger."),
                "ai_response": {"entities": []},
            },
        )

        assert response.status_code == 400, route
        assert response.json()["error"] == error_code
        assert "missing required keys" in response.json()["detail"]


def test_characters_preview_returns_character_profiles() -> None:
    """Character API should expose timeline-aware profile views."""
    client = TestClient(create_app())
    anchor_id = "api_demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor"

    response = client.post(
        "/v2/characters/preview",
        json={
            "source_id": "api_demo",
            "filename": "chapter.txt",
            "content_base64": _b64("Chapter 1\nMark carried a rusty dagger."),
            "ai_response": weapon_payload(anchor_id=anchor_id, weapon="Rusty Dagger"),
            "character_ids": ["character_mark"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_id"] == "api_demo"
    assert payload["scene_id"] == "api_demo_chapter_001_scene_001"
    assert payload["character_profiles"][0]["display_name"] == "Mark"
    assert payload["character_profiles"][0]["current_equipment"]["items"] == [
        "Rusty Dagger"
    ]
    assert "Mark carried a rusty dagger." not in response.text


def test_scenes_preview_returns_scene_sheet() -> None:
    """Scene API should expose a timeline-aware scene sheet."""
    client = TestClient(create_app())
    anchor_id = "api_demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor"

    response = client.post(
        "/v2/scenes/preview",
        json={
            "source_id": "api_demo",
            "filename": "chapter.txt",
            "content_base64": _b64("Chapter 1\nMark carried a rusty dagger."),
            "ai_response": weapon_payload(anchor_id=anchor_id, weapon="Rusty Dagger"),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_id"] == "api_demo"
    assert payload["scene_id"] == "api_demo_chapter_001_scene_001"
    assert payload["scene_sheet"]["characters_present"]["items"] == ["Mark"]
    assert payload["scene_sheet"]["title"]
    assert "Mark carried a rusty dagger." not in response.text


def test_prompts_preview_returns_production_pack() -> None:
    """Prompt API should expose canon-backed production packs."""
    client = TestClient(create_app())
    anchor_id = "api_demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor"

    response = client.post(
        "/v2/prompts/preview",
        json={
            "source_id": "api_demo",
            "filename": "chapter.txt",
            "content_base64": _b64("Chapter 1\nMark carried a rusty dagger."),
            "ai_response": weapon_payload(anchor_id=anchor_id, weapon="Rusty Dagger"),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_id"] == "api_demo"
    assert payload["scene_id"] == "api_demo_chapter_001_scene_001"
    assert payload["production_pack"]["image_prompt"]["title"] == "Image Prompt"
    assert payload["production_pack"]["scene"]["characters_present"]["items"] == [
        "Mark"
    ]
    assert "Mark carried a rusty dagger." not in response.text


def test_continuity_preview_returns_direct_continuity_report() -> None:
    """Continuity API should expose project changes without aggregate outputs."""
    client = TestClient(create_app())
    first_anchor_id = "api_demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor"
    second_anchor_id = "api_demo_chapter_002_scene_001_paragraph_001_sentence_001_anchor"

    response = client.post(
        "/v2/continuity/preview",
        json={
            "source_id": "api_demo",
            "filename": "chapter.txt",
            "content_base64": _b64(
                "Chapter 1\nMark carried a rusty dagger.\n\n"
                "Chapter 2\nMark bought an iron sword."
            ),
            "ai_response": {
                "scenes": {
                    "api_demo_chapter_001_scene_001": weapon_payload(
                        anchor_id=first_anchor_id,
                        weapon="Rusty Dagger",
                    ),
                    "api_demo_chapter_002_scene_001": weapon_payload(
                        anchor_id=second_anchor_id,
                        weapon="Iron Sword",
                    ),
                }
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_id"] == "api_demo"
    assert payload["source_format"] == "txt"
    assert payload["continuity_report"]["source_id"] == "api_demo"
    assert [
        scene["scene_id"] for scene in payload["continuity_report"]["scenes"]
    ] == [
        "api_demo_chapter_001_scene_001",
        "api_demo_chapter_002_scene_001",
    ]
    assert payload["continuity_report"]["scenes"][0]["new"]
    assert payload["continuity_report"]["scenes"][1]["updated"]
    assert "Mark bought an iron sword." not in response.text


def test_project_outputs_preview_returns_presentation_ready_outputs() -> None:
    """Project output preview should expose engine-built user-facing views."""
    client = TestClient(create_app())
    first_anchor_id = "api_demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor"
    second_anchor_id = "api_demo_chapter_002_scene_001_paragraph_001_sentence_001_anchor"

    response = client.post(
        "/v2/project-outputs/preview",
        json={
            "source_id": "api_demo",
            "filename": "chapter.txt",
            "content_base64": _b64(
                "Chapter 1\nMark carried a rusty dagger.\n\n"
                "Chapter 2\nMark bought an iron sword."
            ),
            "ai_response": {
                "scenes": {
                    "api_demo_chapter_001_scene_001": weapon_payload(
                        anchor_id=first_anchor_id,
                        weapon="Rusty Dagger",
                    ),
                    "api_demo_chapter_002_scene_001": weapon_payload(
                        anchor_id=second_anchor_id,
                        weapon="Iron Sword",
                    ),
                }
            },
            "scene_id": "api_demo_chapter_002_scene_001",
            "character_ids": ["character_mark"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_id"] == "api_demo"
    assert payload["source_format"] == "txt"
    assert payload["scene_id"] == "api_demo_chapter_002_scene_001"
    assert payload["character_profiles"][0]["display_name"] == "Mark"
    assert payload["character_profiles"][0]["current_equipment"]["items"] == [
        "Iron Sword"
    ]
    assert payload["scene_sheet"]["characters_present"]["items"] == ["Mark"]
    assert payload["production_pack"]["image_prompt"]["title"] == "Image Prompt"
    assert payload["continuity_report"]["source_id"] == "api_demo"
    assert [
        scene["scene_id"] for scene in payload["continuity_report"]["scenes"]
    ] == [
        "api_demo_chapter_001_scene_001",
        "api_demo_chapter_002_scene_001",
    ]
    assert "Mark bought an iron sword." not in response.text


def test_project_outputs_preview_rejects_unknown_character() -> None:
    """Project output preview should fail clearly for invalid requested IDs."""
    client = TestClient(create_app())
    anchor_id = "api_demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor"

    response = client.post(
        "/v2/project-outputs/preview",
        json={
            "source_id": "api_demo",
            "filename": "chapter.txt",
            "content_base64": _b64("Chapter 1\nMark carried a rusty dagger."),
            "ai_response": weapon_payload(anchor_id=anchor_id, weapon="Rusty Dagger"),
            "character_ids": ["character_unknown"],
        },
    )

    assert response.status_code == 400
    assert response.json()["error"] == "project_output_preview_failed"
    assert "Unknown character" in response.json()["detail"]


def test_world_preview_returns_timeline_aware_world_sheet() -> None:
    """World API should expose presented world state without source prose."""
    client = TestClient(create_app())
    first_anchor_id = "api_demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor"
    second_anchor_id = "api_demo_chapter_002_scene_001_paragraph_001_sentence_001_anchor"

    response = client.post(
        "/v2/world/preview",
        json={
            "source_id": "api_demo",
            "filename": "chapter.txt",
            "content_base64": _b64(
                "Chapter 1\nThe hangar was quiet.\n\n"
                "Chapter 2\nThe hangar alarm was active."
            ),
            "ai_response": {
                "scenes": {
                    "api_demo_chapter_001_scene_001": world_payload(
                        anchor_id=first_anchor_id,
                        condition="Quiet",
                    ),
                    "api_demo_chapter_002_scene_001": world_payload(
                        anchor_id=second_anchor_id,
                        condition="Alarm active",
                    ),
                }
            },
            "scene_id": "api_demo_chapter_002_scene_001",
            "world_entity_ids": ["location_hangar"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_id"] == "api_demo"
    assert payload["source_format"] == "txt"
    assert payload["scene_id"] == "api_demo_chapter_002_scene_001"
    assert payload["world_sheet"]["chapter_label"] == "Chapter 2"
    assert payload["world_sheet"]["entity_sections"][0]["title"] == "Hangar (location)"
    assert "condition: Alarm active" in payload["world_sheet"]["entity_sections"][0]["items"]
    assert "The hangar alarm was active." not in response.text


def test_export_preview_returns_export_engine_markdown() -> None:
    """Export preview should serialize requested outputs through Export Engine."""
    client = TestClient(create_app())
    first_anchor_id = "api_demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor"
    second_anchor_id = "api_demo_chapter_002_scene_001_paragraph_001_sentence_001_anchor"

    response = client.post(
        "/v2/exports/preview",
        json={
            "source_id": "api_demo",
            "filename": "chapter.txt",
            "content_base64": _b64(
                "Chapter 1\nMark carried a rusty dagger.\n\n"
                "Chapter 2\nMark bought an iron sword."
            ),
            "ai_response": {
                "scenes": {
                    "api_demo_chapter_001_scene_001": weapon_payload(
                        anchor_id=first_anchor_id,
                        weapon="Rusty Dagger",
                    ),
                    "api_demo_chapter_002_scene_001": weapon_payload(
                        anchor_id=second_anchor_id,
                        weapon="Iron Sword",
                    ),
                }
            },
            "scene_id": "api_demo_chapter_002_scene_001",
            "character_ids": ["character_mark"],
            "export_kind": "production_pack",
            "export_format": "markdown",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_id"] == "api_demo"
    assert payload["source_format"] == "txt"
    assert payload["export_kind"] == "production_pack"
    assert payload["export_format"] == "markdown"
    assert payload["filename"] == "api_demo_production_pack.md"
    assert payload["content_type"] == "text/markdown; charset=utf-8"
    assert "# Scene 1" in payload["content"]
    assert "## Image Prompt" in payload["content"]
    assert "Mark bought an iron sword." not in payload["content"]


def test_export_preview_redacts_continuity_report_quotes() -> None:
    """Export preview should not leak exact source prose in continuity reports."""
    client = TestClient(create_app())
    first_anchor_id = "api_demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor"
    second_anchor_id = "api_demo_chapter_002_scene_001_paragraph_001_sentence_001_anchor"

    response = client.post(
        "/v2/exports/preview",
        json={
            "source_id": "api_demo",
            "filename": "chapter.txt",
            "content_base64": _b64(
                "Chapter 1\nMark carried a rusty dagger.\n\n"
                "Chapter 2\nMark bought an iron sword."
            ),
            "ai_response": {
                "scenes": {
                    "api_demo_chapter_001_scene_001": weapon_payload(
                        anchor_id=first_anchor_id,
                        weapon="Rusty Dagger",
                    ),
                    "api_demo_chapter_002_scene_001": weapon_payload(
                        anchor_id=second_anchor_id,
                        weapon="Iron Sword",
                    ),
                }
            },
            "export_kind": "continuity_report",
            "export_format": "json",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    content = json.loads(payload["content"])
    first_record = content["scenes"][0]["new"][1]
    assert first_record["evidence_id"] == f"evidence_{first_anchor_id}"
    assert first_record["chapter_id"] == "api_demo_chapter_001"
    assert first_record["evidence_quote"] == ""
    assert "Mark carried a rusty dagger." not in payload["content"]
    assert "Mark bought an iron sword." not in payload["content"]


def test_export_preview_rejects_unsupported_export_combination() -> None:
    """Export preview should fail clearly for unsupported kind/format pairs."""
    client = TestClient(create_app())
    anchor_id = "api_demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor"

    response = client.post(
        "/v2/exports/preview",
        json={
            "source_id": "api_demo",
            "filename": "chapter.txt",
            "content_base64": _b64("Chapter 1\nMark carried a rusty dagger."),
            "ai_response": weapon_payload(anchor_id=anchor_id, weapon="Rusty Dagger"),
            "export_kind": "scene_sheet",
            "export_format": "pdf",
        },
    )

    assert response.status_code == 400
    assert response.json()["error"] == "export_preview_failed"
    assert "Unsupported export preview" in response.json()["detail"]


def _workflow_log_record(
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


def _assert_duration_log(record: logging.LogRecord) -> None:
    """Assert a workflow log record has metadata-only duration."""
    duration_ms = getattr(record, "duration_ms", None)
    assert isinstance(duration_ms, float)
    assert duration_ms >= 0.0


def _caplog_record_text(caplog: LogCaptureFixture) -> str:
    """Return captured log messages and extras as searchable text."""
    return "\n".join(str(record.__dict__) for record in caplog.records)


def _b64(value: str) -> str:
    """Return base64 text for API import tests."""
    return base64.b64encode(value.encode("utf-8")).decode("ascii")


def world_payload(anchor_id: str, condition: str) -> dict[str, Any]:
    """Build an evidence-bounded world entity payload for API tests."""
    normalized_condition = condition.lower().replace(" ", "_")
    return {
        "entities": [
            {
                "entity_id": "location_hangar",
                "entity_type": "location",
                "display_name": "Hangar",
                "evidence_anchor_id": anchor_id,
                "confidence": 0.95,
            }
        ],
        "facts": [
            {
                "fact_id": f"fact_location_hangar_condition_{normalized_condition}",
                "entity_id": "location_hangar",
                "attribute": "condition",
                "value": condition,
                "evidence_anchor_id": anchor_id,
                "confidence": 0.95,
            }
        ],
        "relationships": [],
        "state_changes": [],
    }


def weapon_payload(anchor_id: str, weapon: str) -> dict[str, Any]:
    """Build an evidence-bounded weapon payload for API tests."""
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
