"""Tests for the Aevryn V2 Backend API contract."""

from __future__ import annotations

import base64
from typing import Any

from fastapi.testclient import TestClient

from aevryn.api import create_app, create_app_from_env


def test_health_endpoint_reports_api_status() -> None:
    """Health endpoint should not require engine state."""
    client = TestClient(create_app())

    response = client.get("/v2/health")

    assert response.status_code == 200
    assert response.json() == {
        "api_version": "v2",
        "engine": "Aevryn",
        "status": "ok",
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


def test_create_app_from_env_rejects_wildcard_cors_origin() -> None:
    """Environment app factory should not allow broad CORS by accident."""
    try:
        create_app_from_env({"AEVRYN_API_ALLOWED_ORIGINS": "*"})
    except ValueError as error:
        assert "cannot include '*'" in str(error)
    else:
        raise AssertionError("Expected wildcard CORS origin to be rejected.")


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
    assert "No persistent Project Database yet." in payload["platform_limits"]


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
    assert "/v2/project-outputs/preview" in route_paths
    assert "/v2/exports/preview" in route_paths
    assert ".epub" in {
        item["extension"] for item in payload["source_formats"]["supported"]
    }
    assert export_capabilities["prompt_bundle"] == ["markdown", "json", "csv"]
    assert "No persistent Project Database yet." in payload["platform_limits"]


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
    assert paths["/v2/imports/inspect"]["post"]["operationId"] == (
        "postV2ImportsInspect"
    )
    assert paths["/v2/imports/inspect"]["post"]["tags"] == ["Import"]
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


def _b64(value: str) -> str:
    """Return base64 text for API import tests."""
    return base64.b64encode(value.encode("utf-8")).decode("ascii")


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
