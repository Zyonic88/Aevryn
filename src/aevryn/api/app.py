"""FastAPI application for the Aevryn Backend API."""

from __future__ import annotations

import base64
import binascii
import json
import os
import tempfile
import uuid
from collections.abc import Awaitable, Callable, Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException

from aevryn.api.models import (
    ApiIndexResponse,
    ApiLink,
    ApiRouteCapability,
    CapabilitiesResponse,
    CharacterProfileOutput,
    ContinuityRecordOutput,
    ContinuityReportOutput,
    ContinuitySceneOutput,
    ErrorResponse,
    EvidenceAnchorPreview,
    ExportCapability,
    ExportPreviewRequest,
    ExportPreviewResponse,
    ExtractionApplyRequest,
    ExtractionApplyResponse,
    ExtractionPromptRequest,
    ExtractionPromptResponse,
    ExtractionSceneResult,
    HealthResponse,
    ImportInspectRequest,
    ImportInspectResponse,
    OutputSection,
    ProductionPackOutput,
    ProjectOutputsPreviewRequest,
    ProjectOutputsPreviewResponse,
    SceneMapEntry,
    SceneSheetOutput,
    SourceFormat,
    SourceFormatsResponse,
    WorldSheetOutput,
)
from aevryn.export import ExportEngine
from aevryn.extraction import EvidenceBoundedAIExtractor, StaticAIExtractionClient
from aevryn.importing import ImportedSource, SourceFileTextExtractor
from aevryn.presentation import (
    CharacterProfileView,
    PresentationEngine,
    PresentationSection,
    ProductionPackView,
    SceneSheetView,
    WorldSheetView,
)
from aevryn.projects import AevrynProjectRunner, ProjectRunResult
from aevryn.projects.runner import ContinuityRecord, ContinuityReport, ContinuitySceneReport
from aevryn.prompts import CanonPromptBuilder, ProductionPack

API_VERSION = "v2"
ALLOWED_ORIGINS_ENV = "AEVRYN_API_ALLOWED_ORIGINS"


def create_app_from_env(environ: Mapping[str, str] | None = None) -> FastAPI:
    """Create the Backend API application from deployment environment settings.

    Parameters:
        environ: Optional environment mapping. Defaults to ``os.environ``.

    Returns:
        Configured FastAPI application.

    Raises:
        ValueError: If configured CORS origins are unsafe or invalid.
    """
    return create_app(
        allowed_origins=_allowed_origins_from_env(environ or os.environ),
    )


def create_app(allowed_origins: Sequence[str] = ()) -> FastAPI:
    """Create the Aevryn Backend API application.

    Parameters:
        allowed_origins: Optional browser origins allowed by CORS middleware.

    Returns:
        Configured FastAPI application.
    """
    app = FastAPI(
        title="Aevryn Backend API",
        version="2.0.0",
        description=(
            "Version 2 API contract for using the Aevryn Engine through "
            "platform clients."
        ),
        responses={
            400: {"model": ErrorResponse},
            422: {"model": ErrorResponse},
        },
    )
    if allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(allowed_origins),
            allow_credentials=True,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["*"],
        )

    @app.middleware("http")
    async def api_identity_headers(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Attach stable Aevryn identity headers to every API response."""
        request_id = _request_id(request)
        response = await call_next(request)
        response.headers["X-Aevryn-API-Version"] = API_VERSION
        response.headers["X-Aevryn-Engine"] = "Aevryn"
        response.headers["X-Request-ID"] = request_id
        return response

    @app.exception_handler(StarletteHTTPException)
    def http_error_handler(
        _request: Request,
        error: StarletteHTTPException,
    ) -> JSONResponse:
        """Return stable top-level API error responses."""
        detail = error.detail
        if isinstance(detail, dict):
            error_code = str(detail.get("error", "request_failed"))
            error_detail = str(detail.get("detail", error_code))
        else:
            error_code = "request_failed"
            error_detail = str(detail)

        return JSONResponse(
            status_code=error.status_code,
            content=ErrorResponse(error=error_code, detail=error_detail).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    def validation_error_handler(
        _request: Request,
        error: RequestValidationError,
    ) -> JSONResponse:
        """Return stable validation errors for malformed API requests."""
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error="invalid_request",
                detail=_validation_error_detail(error),
            ).model_dump(),
        )

    @app.get(
        "/v2",
        response_model=ApiIndexResponse,
        tags=["System"],
        operation_id="getV2Index",
    )
    def api_index() -> ApiIndexResponse:
        """Return the Version 2 API index."""
        return ApiIndexResponse(
            api_version=API_VERSION,
            engine="Aevryn",
            phase="v2_phase_1_backend_api",
            links=(
                ApiLink(rel="health", href="/v2/health", method="GET"),
                ApiLink(rel="capabilities", href="/v2/capabilities", method="GET"),
                ApiLink(rel="source_formats", href="/v2/source-formats", method="GET"),
                ApiLink(rel="openapi", href="/openapi.json", method="GET"),
            ),
            platform_limits=_platform_limits(),
        )

    @app.get(
        "/v2/health",
        response_model=HealthResponse,
        tags=["System"],
        operation_id="getV2Health",
    )
    def health() -> HealthResponse:
        """Return API health without touching engine state."""
        return HealthResponse(
            status="ok",
            api_version=API_VERSION,
            engine="Aevryn",
        )

    @app.get(
        "/v2/capabilities",
        response_model=CapabilitiesResponse,
        tags=["System"],
        operation_id="getV2Capabilities",
    )
    def capabilities() -> CapabilitiesResponse:
        """Return discoverable Backend API capability metadata."""
        return CapabilitiesResponse(
            api_version=API_VERSION,
            engine="Aevryn",
            phase="v2_phase_1_backend_api",
            routes=_route_capabilities(),
            source_formats=_source_formats_response(),
            export_capabilities=_export_capabilities(),
            platform_limits=_platform_limits(),
        )

    @app.get(
        "/v2/source-formats",
        response_model=SourceFormatsResponse,
        tags=["Import"],
        operation_id="getV2SourceFormats",
    )
    def source_formats() -> SourceFormatsResponse:
        """Return native source-format support metadata."""
        return _source_formats_response()

    @app.post(
        "/v2/imports/inspect",
        response_model=ImportInspectResponse,
        tags=["Import"],
        operation_id="postV2ImportsInspect",
    )
    def inspect_import(request: ImportInspectRequest) -> ImportInspectResponse:
        """Inspect source structure through Project Manager and Story Import."""
        imported_source, source_format = _import_request_source(request)

        return _import_response(
            source_format=source_format,
            imported_source=imported_source,
        )

    @app.post(
        "/v2/extraction-prompts",
        response_model=ExtractionPromptResponse,
        tags=["Extraction"],
        operation_id="postV2ExtractionPrompts",
    )
    def extraction_prompt(
        request: ExtractionPromptRequest,
    ) -> ExtractionPromptResponse:
        """Build an evidence-bounded AI extraction prompt through the engine."""
        imported_source, source_format = _import_request_source(request)
        try:
            extraction_input = AevrynProjectRunner().build_scene_extraction_input(
                imported_source=imported_source,
                scene_id=request.scene_id,
            )
        except ValueError as error:
            raise HTTPException(
                status_code=400,
                detail={"error": "extraction_prompt_failed", "detail": str(error)},
            ) from error

        prompt = EvidenceBoundedAIExtractor(
            client=StaticAIExtractionClient("{}")
        ).build_prompt(extraction_input)
        return ExtractionPromptResponse(
            source_id=imported_source.source_id,
            source_format=source_format,
            scene_id=extraction_input.scene_id,
            evidence_anchor_count=len(extraction_input.evidence_anchor_ids),
            prompt=prompt,
        )

    @app.post(
        "/v2/extractions/apply",
        response_model=ExtractionApplyResponse,
        tags=["Extraction"],
        operation_id="postV2ExtractionsApply",
    )
    def apply_extraction(
        request: ExtractionApplyRequest,
    ) -> ExtractionApplyResponse:
        """Apply evidence-bounded AI candidates through Canon Updating."""
        try:
            result, _source_format = _run_project_result(request)
        except ValueError as error:
            raise HTTPException(
                status_code=400,
                detail={"error": "extraction_apply_failed", "detail": str(error)},
            ) from error

        return _extraction_apply_response(result)

    @app.post(
        "/v2/project-outputs/preview",
        response_model=ProjectOutputsPreviewResponse,
        tags=["Project Outputs"],
        operation_id="postV2ProjectOutputsPreview",
    )
    def preview_project_outputs(
        request: ProjectOutputsPreviewRequest,
    ) -> ProjectOutputsPreviewResponse:
        """Preview platform-ready outputs through the Aevryn Engine."""
        try:
            result, source_format = _run_project_result(request)
            runner = AevrynProjectRunner()
            scene_id = request.scene_id or runner.latest_scene_id(result)
            character_ids = request.character_ids or _accepted_character_ids(result)
            context = runner.build_scene_context(
                result=result,
                scene_id=scene_id,
                character_ids=character_ids,
            )
            pack = CanonPromptBuilder().build_production_pack(context)
            presenter = PresentationEngine()
            scene_sheet = presenter.scene_sheet(context=context, analysis=pack.analysis)
            source_quotes = _source_quotes(result)
            world_state = runner.build_world_state_at_scene(
                result=result,
                entity_ids=request.world_entity_ids,
                scene_id=scene_id,
            )
            return ProjectOutputsPreviewResponse(
                source_id=result.imported_source.source_id,
                source_format=source_format,
                scene_id=scene_id,
                character_profiles=tuple(
                    _character_profile_output(
                        presenter.character_profile(
                            runner.build_character_card_at_scene(
                                result=result,
                                character_id=character_id,
                                scene_id=scene_id,
                            )
                        )
                    )
                    for character_id in character_ids
                ),
                scene_sheet=_scene_sheet_output(scene_sheet, source_quotes=source_quotes),
                production_pack=_production_pack_output(
                    presenter.production_pack(pack=pack, scene=scene_sheet),
                    source_quotes=source_quotes,
                ),
                world_sheet=_world_sheet_output(presenter.world_sheet(world_state)),
                continuity_report=_continuity_report_output(
                    runner.build_continuity_report(result)
                ),
            )
        except ValueError as error:
            raise HTTPException(
                status_code=400,
                detail={"error": "project_output_preview_failed", "detail": str(error)},
            ) from error

    @app.post(
        "/v2/exports/preview",
        response_model=ExportPreviewResponse,
        tags=["Exports"],
        operation_id="postV2ExportsPreview",
    )
    def preview_export(request: ExportPreviewRequest) -> ExportPreviewResponse:
        """Preview one serialized export through the Export Engine."""
        try:
            result, source_format = _run_project_result(request)
            return _export_preview_response(
                request=request,
                result=result,
                source_format=source_format,
            )
        except ValueError as error:
            raise HTTPException(
                status_code=400,
                detail={"error": "export_preview_failed", "detail": str(error)},
            ) from error

    return app


def _decode_base64(value: str) -> bytes:
    """Decode base64 API content or raise a stable HTTP error."""
    try:
        return base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as error:
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_base64", "detail": "content_base64 is invalid."},
        ) from error


def _validation_error_detail(error: RequestValidationError) -> str:
    """Return a concise validation error detail string."""
    first_error = error.errors()[0] if error.errors() else {}
    location = ".".join(str(part) for part in first_error.get("loc", ()))
    message = str(first_error.get("msg", "Request validation failed."))
    if location:
        return f"{location}: {message}"

    return message


def _request_id(request: Request) -> str:
    """Return client request ID or generate one for response tracing."""
    request_id = request.headers.get("X-Request-ID", "").strip()
    if request_id and not any(character.isspace() for character in request_id):
        return request_id

    return uuid.uuid4().hex


def _allowed_origins_from_env(environ: Mapping[str, str]) -> tuple[str, ...]:
    """Return allowed CORS origins from deployment environment settings."""
    raw_value = environ.get(ALLOWED_ORIGINS_ENV, "")
    origins = tuple(
        origin.strip()
        for origin in raw_value.split(",")
        if origin.strip()
    )
    if any(origin == "*" for origin in origins):
        raise ValueError("AEVRYN_API_ALLOWED_ORIGINS cannot include '*'.")

    return origins


def _platform_limits() -> tuple[str, ...]:
    """Return current Phase 1 platform limits."""
    return (
        "Stateless preview routes only.",
        "No persistent Project Database yet.",
        "No authentication enforcement yet.",
        "No background worker queue yet.",
        "No website or frontend runtime yet.",
    )


def _route_capabilities() -> tuple[ApiRouteCapability, ...]:
    """Return public route capability metadata."""
    return (
        ApiRouteCapability(
            method="GET",
            path="/v2",
            purpose="Report Version 2 API index links.",
        ),
        ApiRouteCapability(
            method="GET",
            path="/v2/health",
            purpose="Report API health without touching engine state.",
        ),
        ApiRouteCapability(
            method="GET",
            path="/v2/capabilities",
            purpose="Report discoverable Phase 1 API capabilities.",
        ),
        ApiRouteCapability(
            method="GET",
            path="/v2/source-formats",
            purpose="Report supported and deferred source formats.",
        ),
        ApiRouteCapability(
            method="POST",
            path="/v2/imports/inspect",
            purpose="Inspect source structure without returning source prose.",
        ),
        ApiRouteCapability(
            method="POST",
            path="/v2/extraction-prompts",
            purpose="Build evidence-bounded extraction prompts.",
        ),
        ApiRouteCapability(
            method="POST",
            path="/v2/extractions/apply",
            purpose="Apply extraction candidates through Canon Updating.",
        ),
        ApiRouteCapability(
            method="POST",
            path="/v2/project-outputs/preview",
            purpose="Preview presentation-ready engine outputs.",
        ),
        ApiRouteCapability(
            method="POST",
            path="/v2/exports/preview",
            purpose="Preview serialized exports through Export Engine.",
        ),
    )


def _source_formats_response() -> SourceFormatsResponse:
    """Return native source-format support metadata."""
    return SourceFormatsResponse(
        supported=(
            SourceFormat(
                extension=".txt",
                status="supported",
                adapter="SourceFileTextExtractor",
                evidence_anchor_status="supported",
                notes="Read as UTF-8 text and passed directly to Story Import.",
            ),
            SourceFormat(
                extension=".md/.markdown",
                status="supported",
                adapter="SourceFileTextExtractor",
                evidence_anchor_status="supported",
                notes="Read as UTF-8 text; Markdown markers remain source text.",
            ),
            SourceFormat(
                extension=".html/.htm/.xhtml",
                status="supported",
                adapter="SourceFileTextExtractor",
                evidence_anchor_status="supported",
                notes="Extracts visible text and skips script, style, and navigation.",
            ),
            SourceFormat(
                extension=".fb2",
                status="supported",
                adapter="SourceFileTextExtractor",
                evidence_anchor_status="supported",
                notes="Extracts paragraph-like XML text.",
            ),
            SourceFormat(
                extension=".docx",
                status="supported",
                adapter="SourceFileTextExtractor",
                evidence_anchor_status="supported",
                notes="Extracts paragraph text from word/document.xml.",
            ),
            SourceFormat(
                extension=".odt",
                status="supported",
                adapter="SourceFileTextExtractor",
                evidence_anchor_status="supported",
                notes="Extracts heading and paragraph text from content.xml.",
            ),
            SourceFormat(
                extension=".epub",
                status="supported",
                adapter="EpubTextExtractor",
                evidence_anchor_status="supported",
                notes="Extracts readable spine content and skips navigation material.",
            ),
        ),
        deferred=(
            SourceFormat(
                extension=".pdf",
                status="deferred",
                adapter="none",
                evidence_anchor_status="not_enabled",
                notes="Requires deterministic PDF reading-order parser support.",
            ),
            SourceFormat(
                extension=".mobi",
                status="deferred",
                adapter="none",
                evidence_anchor_status="not_enabled",
                notes="Requires dedicated Kindle parser support.",
            ),
            SourceFormat(
                extension=".azw3",
                status="deferred",
                adapter="none",
                evidence_anchor_status="not_enabled",
                notes="Requires dedicated Kindle parser support.",
            ),
        ),
    )


def _export_capabilities() -> tuple[ExportCapability, ...]:
    """Return export kinds and formats supported by Phase 1 preview."""
    return (
        ExportCapability(export_kind="character_profile", formats=("markdown",)),
        ExportCapability(export_kind="scene_sheet", formats=("markdown",)),
        ExportCapability(export_kind="production_pack", formats=("markdown",)),
        ExportCapability(export_kind="world_sheet", formats=("markdown",)),
        ExportCapability(export_kind="prompt_bundle", formats=("markdown", "json", "csv")),
        ExportCapability(export_kind="continuity_report", formats=("markdown", "json")),
    )


def _import_request_source(
    request: ImportInspectRequest,
) -> tuple[ImportedSource, str]:
    """Import source content from a request through Project Manager."""
    source_bytes = _decode_base64(request.content_base64)
    with tempfile.TemporaryDirectory(prefix="AEVRYN_api_import_") as directory:
        source_path = Path(directory) / Path(request.filename).name
        source_path.write_bytes(source_bytes)
        try:
            imported_source = AevrynProjectRunner().import_text_file(
                path=source_path,
                source_id=request.source_id,
                title=request.title,
            )
            source_format = SourceFileTextExtractor.source_format_for_path(
                source_path
            )
        except ValueError as error:
            raise HTTPException(
                status_code=400,
                detail={"error": "import_failed", "detail": str(error)},
            ) from error

    return imported_source, source_format


def _run_project_result(
    request: ExtractionApplyRequest,
) -> tuple[ProjectRunResult, str]:
    """Run a stateless project workflow from an API extraction request."""
    imported_source, source_format = _import_request_source(request)
    runner = AevrynProjectRunner()
    scene_payloads = _scene_payloads_from_response(request.ai_response)
    if scene_payloads is not None:
        return (
            runner.run_imported_source_with_scene_payloads(
                imported_source=imported_source,
                payloads_by_scene_id=scene_payloads,
            ),
            source_format,
        )

    return (
        runner.run_imported_scene(
            imported_source=imported_source,
            extractor=EvidenceBoundedAIExtractor(
                client=StaticAIExtractionClient(
                    json.dumps(request.ai_response, sort_keys=True)
                )
            ),
            scene_id=request.scene_id,
        ),
        source_format,
    )


def _import_response(
    source_format: str,
    imported_source: ImportedSource,
) -> ImportInspectResponse:
    """Build an import inspection response from Story Import output."""
    source = imported_source
    scene_count = sum(len(chapter.scenes) for chapter in source.story.chapters)
    return ImportInspectResponse(
        source_id=source.source_id,
        source_format=source_format,
        title=source.title,
        chapters=len(source.story.chapters),
        chapter_ids=tuple(chapter.chapter_id for chapter in source.story.chapters),
        scenes=scene_count,
        scene_ids=tuple(
            scene.scene_id
            for chapter in source.story.chapters
            for scene in chapter.scenes
        ),
        scene_map=tuple(
            SceneMapEntry(
                chapter_id=chapter.chapter_id,
                chapter_index=chapter.chapter_index,
                scene_id=scene.scene_id,
                scene_index=scene.scene_index,
                title=scene.title,
            )
            for chapter in source.story.chapters
            for scene in chapter.scenes
        ),
        paragraphs=len(source.paragraphs),
        evidence_anchors=len(source.anchors),
        first_evidence_anchors=tuple(
            EvidenceAnchorPreview(
                anchor_id=anchor.anchor_id,
                chapter_id=anchor.chapter_id,
                scene_id=anchor.scene_id,
                paragraph_index=anchor.paragraph_index,
                sentence_index=anchor.sentence_index,
            )
            for anchor in source.anchors[:5]
        ),
    )


def _extraction_apply_response(result: ProjectRunResult) -> ExtractionApplyResponse:
    """Build an extraction application summary response."""
    return ExtractionApplyResponse(
        results=tuple(
            ExtractionSceneResult(
                scene_id=extraction.scene_id,
                entities=len(extraction.entities),
                facts=len(extraction.facts),
                relationships=len(extraction.relationships),
                state_changes=len(extraction.state_changes),
            )
            for extraction in result.extraction_results
        ),
        accepted_entities=sum(
            len(summary.accepted_entities) for summary in result.update_summaries
        ),
        accepted_entity_ids=_summary_ids(
            summary.accepted_entities for summary in result.update_summaries
        ),
        accepted_facts=sum(
            len(summary.accepted_facts) for summary in result.update_summaries
        ),
        accepted_fact_ids=_summary_ids(
            summary.accepted_facts for summary in result.update_summaries
        ),
        accepted_relationships=sum(
            len(summary.accepted_relationships)
            for summary in result.update_summaries
        ),
        accepted_relationship_ids=_summary_ids(
            summary.accepted_relationships for summary in result.update_summaries
        ),
        accepted_state_changes=sum(
            len(summary.accepted_state_changes)
            for summary in result.update_summaries
        ),
        accepted_state_change_ids=_summary_ids(
            summary.accepted_state_changes for summary in result.update_summaries
        ),
        rejected_candidate_ids=_summary_ids(
            summary.rejected_candidates for summary in result.update_summaries
        ),
    )


def _accepted_character_ids(result: ProjectRunResult) -> tuple[str, ...]:
    """Return accepted character IDs in first-seen scene order."""
    character_ids: dict[str, None] = {}
    for summary in result.update_summaries:
        for entity_id in summary.accepted_entities:
            if result.database.retrieve_character(entity_id) is not None:
                character_ids.setdefault(entity_id, None)

    return tuple(character_ids)


def _source_quotes(result: ProjectRunResult) -> tuple[str, ...]:
    """Return normalized source quotes that should not leak in preview outputs."""
    return tuple(
        " ".join(anchor.quote.split())
        for anchor in result.imported_source.anchors
        if anchor.quote.strip()
    )


def _section_output(
    section: PresentationSection,
    source_quotes: Sequence[str] = (),
) -> OutputSection:
    """Convert a presentation section to an API output section."""
    return OutputSection(
        title=section.title,
        items=tuple(_redact_source_quote(item, source_quotes) for item in section.items),
    )


def _redact_source_quote(value: str, source_quotes: Sequence[str]) -> str:
    """Return a safe preview value without exact source prose."""
    normalized = " ".join(value.split())
    for quote in source_quotes:
        if len(quote) >= 20 and (
            quote in normalized or (len(normalized) >= 20 and normalized in quote)
        ):
            return "Source-backed detail available through evidence controls."

    return value


def _character_profile_output(
    profile: CharacterProfileView,
) -> CharacterProfileOutput:
    """Convert a character profile view to the API contract."""
    return CharacterProfileOutput(
        character_id=profile.character_id,
        display_name=profile.display_name,
        subtitle=profile.subtitle,
        status=_section_output(profile.status),
        current_goal=_section_output(profile.current_goal),
        current_equipment=_section_output(profile.current_equipment),
        current_abilities=_section_output(profile.current_abilities),
        current_assets=_section_output(profile.current_assets),
        territory=_section_output(profile.territory),
        relationships=_section_output(profile.relationships),
        current_limitations=_section_output(profile.current_limitations),
        recent_changes=_section_output(profile.recent_changes),
        evidence_summary=profile.evidence_summary,
    )


def _scene_sheet_output(
    scene: SceneSheetView,
    source_quotes: Sequence[str] = (),
) -> SceneSheetOutput:
    """Convert a scene sheet view to the API contract."""
    return SceneSheetOutput(
        scene_id=scene.scene_id,
        title=scene.title,
        chapter_label=scene.chapter_label,
        location=_section_output(scene.location, source_quotes=source_quotes),
        characters_present=_section_output(
            scene.characters_present,
            source_quotes=source_quotes,
        ),
        mood=_section_output(scene.mood, source_quotes=source_quotes),
        purpose=_section_output(scene.purpose, source_quotes=source_quotes),
        visual_highlights=_section_output(
            scene.visual_highlights,
            source_quotes=source_quotes,
        ),
        continuity_changes=_section_output(
            scene.continuity_changes,
            source_quotes=source_quotes,
        ),
        environment=_section_output(scene.environment, source_quotes=source_quotes),
        evidence_summary=scene.evidence_summary,
    )


def _production_pack_output(
    pack: ProductionPackView,
    source_quotes: Sequence[str] = (),
) -> ProductionPackOutput:
    """Convert a production pack view to the API contract."""
    return ProductionPackOutput(
        scene=_scene_sheet_output(pack.scene, source_quotes=source_quotes),
        image_prompt=_section_output(pack.image_prompt, source_quotes=source_quotes),
        narration_prompt=_section_output(
            pack.narration_prompt,
            source_quotes=source_quotes,
        ),
        camera_prompt=_section_output(pack.camera_prompt, source_quotes=source_quotes),
        animation_prompt=_section_output(
            pack.animation_prompt,
            source_quotes=source_quotes,
        ),
    )


def _world_sheet_output(world: WorldSheetView) -> WorldSheetOutput:
    """Convert a world sheet view to the API contract."""
    return WorldSheetOutput(
        chapter_label=world.chapter_label,
        entity_sections=tuple(
            _section_output(section) for section in world.entity_sections
        ),
        evidence_summary=world.evidence_summary,
    )


def _continuity_record_output(record: ContinuityRecord) -> ContinuityRecordOutput:
    """Convert one continuity record to the API contract."""
    return ContinuityRecordOutput(
        record_id=record.record_id,
        record_type=record.record_type,
        description=record.description,
        evidence_id=record.evidence_id,
        chapter_id=record.chapter_id,
        scene_id=record.scene_id,
    )


def _continuity_scene_output(scene: ContinuitySceneReport) -> ContinuitySceneOutput:
    """Convert one continuity scene report to the API contract."""
    return ContinuitySceneOutput(
        scene_id=scene.scene_id,
        new=tuple(_continuity_record_output(record) for record in scene.new),
        updated=tuple(_continuity_record_output(record) for record in scene.updated),
        still_known=tuple(
            _continuity_record_output(record) for record in scene.still_known
        ),
        invalidated=tuple(
            _continuity_record_output(record) for record in scene.invalidated
        ),
    )


def _continuity_report_output(report: ContinuityReport) -> ContinuityReportOutput:
    """Convert a continuity report to the API contract."""
    return ContinuityReportOutput(
        source_id=report.source_id,
        scenes=tuple(_continuity_scene_output(scene) for scene in report.scenes),
    )


def _export_preview_response(
    request: ExportPreviewRequest,
    result: ProjectRunResult,
    source_format: str,
) -> ExportPreviewResponse:
    """Build one serialized export preview through the Export Engine."""
    runner = AevrynProjectRunner()
    scene_id = request.scene_id or runner.latest_scene_id(result)
    character_ids = request.character_ids or _accepted_character_ids(result)
    context = runner.build_scene_context(
        result=result,
        scene_id=scene_id,
        character_ids=character_ids,
    )
    pack = CanonPromptBuilder().build_production_pack(context)
    presenter = PresentationEngine()
    scene_sheet = presenter.scene_sheet(context=context, analysis=pack.analysis)
    source_quotes = _source_quotes(result)
    safe_scene_sheet = _safe_scene_sheet_view(
        scene=scene_sheet,
        source_quotes=source_quotes,
    )
    production_pack = presenter.production_pack(pack=pack, scene=scene_sheet)
    safe_production_pack = _safe_production_pack_view(
        pack=production_pack,
        source_quotes=source_quotes,
    )
    export_engine = ExportEngine()

    kind = request.export_kind.strip().lower()
    export_format = request.export_format.strip().lower()
    content = _serialized_export_content(
        export_engine=export_engine,
        kind=kind,
        export_format=export_format,
        request=request,
        result=result,
        runner=runner,
        scene_id=scene_id,
        presenter=presenter,
        safe_scene_sheet=safe_scene_sheet,
        safe_production_pack=safe_production_pack,
        pack=pack,
    )

    return ExportPreviewResponse(
        source_id=result.imported_source.source_id,
        source_format=source_format,
        scene_id=scene_id,
        export_kind=kind,
        export_format=export_format,
        filename=f"{result.imported_source.source_id}_{kind}.{_file_extension(export_format)}",
        content_type=_content_type(export_format),
        content=content,
    )


def _serialized_export_content(
    export_engine: ExportEngine,
    kind: str,
    export_format: str,
    request: ExportPreviewRequest,
    result: ProjectRunResult,
    runner: AevrynProjectRunner,
    scene_id: str,
    presenter: PresentationEngine,
    safe_scene_sheet: SceneSheetView,
    safe_production_pack: ProductionPackView,
    pack: ProductionPack,
) -> str:
    """Return serialized export content for a supported kind and format."""
    if kind == "character_profile" and export_format == "markdown":
        character_id = request.character_id or _first_character_id(request, result)
        profile = presenter.character_profile(
            runner.build_character_card_at_scene(
                result=result,
                character_id=character_id,
                scene_id=scene_id,
            )
        )
        return export_engine.character_profile_markdown(profile)

    if kind == "scene_sheet" and export_format == "markdown":
        return export_engine.scene_sheet_view_markdown(safe_scene_sheet)

    if kind == "production_pack" and export_format == "markdown":
        return export_engine.production_pack_view_markdown(safe_production_pack)

    if kind == "world_sheet" and export_format == "markdown":
        world_state = runner.build_world_state_at_scene(
            result=result,
            entity_ids=request.world_entity_ids,
            scene_id=scene_id,
        )
        return export_engine.world_sheet_view_markdown(
            presenter.world_sheet(world_state)
        )

    if kind == "prompt_bundle":
        if export_format == "markdown":
            return export_engine.prompt_sheet_markdown(pack.prompt_bundle)
        if export_format == "json":
            return export_engine.prompt_bundle_json(pack.prompt_bundle)
        if export_format == "csv":
            return export_engine.prompt_bundle_csv(pack.prompt_bundle)

    if kind == "continuity_report":
        report = runner.build_continuity_report(result)
        if export_format == "markdown":
            return export_engine.continuity_report_markdown(report)
        if export_format == "json":
            return export_engine.continuity_report_json(report)

    raise ValueError(f"Unsupported export preview: {kind}/{export_format}")


def _first_character_id(
    request: ProjectOutputsPreviewRequest,
    result: ProjectRunResult,
) -> str:
    """Return the requested or accepted first character ID."""
    character_ids = request.character_ids or _accepted_character_ids(result)
    if not character_ids:
        raise ValueError("At least one character is required for this export.")

    return character_ids[0]


def _safe_scene_sheet_view(
    scene: SceneSheetView,
    source_quotes: Sequence[str],
) -> SceneSheetView:
    """Return a scene sheet with exact source prose redacted."""
    return SceneSheetView(
        scene_id=scene.scene_id,
        title=scene.title,
        chapter_label=scene.chapter_label,
        location=_safe_section(scene.location, source_quotes),
        characters_present=_safe_section(scene.characters_present, source_quotes),
        mood=_safe_section(scene.mood, source_quotes),
        purpose=_safe_section(scene.purpose, source_quotes),
        visual_highlights=_safe_section(scene.visual_highlights, source_quotes),
        continuity_changes=_safe_section(scene.continuity_changes, source_quotes),
        environment=_safe_section(scene.environment, source_quotes),
        evidence_summary=scene.evidence_summary,
    )


def _safe_production_pack_view(
    pack: ProductionPackView,
    source_quotes: Sequence[str],
) -> ProductionPackView:
    """Return a production pack view with exact source prose redacted."""
    return ProductionPackView(
        scene=_safe_scene_sheet_view(pack.scene, source_quotes),
        image_prompt=_safe_section(pack.image_prompt, source_quotes),
        narration_prompt=_safe_section(pack.narration_prompt, source_quotes),
        camera_prompt=_safe_section(pack.camera_prompt, source_quotes),
        animation_prompt=_safe_section(pack.animation_prompt, source_quotes),
    )


def _safe_section(
    section: PresentationSection,
    source_quotes: Sequence[str],
) -> PresentationSection:
    """Return a presentation section with exact source prose redacted."""
    return PresentationSection(
        title=section.title,
        items=tuple(_redact_source_quote(item, source_quotes) for item in section.items),
    )


def _content_type(export_format: str) -> str:
    """Return content type for a supported export format."""
    if export_format == "markdown":
        return "text/markdown; charset=utf-8"
    if export_format == "json":
        return "application/json"
    if export_format == "csv":
        return "text/csv; charset=utf-8"

    raise ValueError(f"Unsupported export format: {export_format}")


def _file_extension(export_format: str) -> str:
    """Return file extension for a supported export format."""
    if export_format == "markdown":
        return "md"
    if export_format in {"json", "csv"}:
        return export_format

    raise ValueError(f"Unsupported export format: {export_format}")


def _scene_payloads_from_response(
    payload: dict[str, Any],
) -> dict[str, dict[str, Any]] | None:
    """Return scene payloads from a multi-scene response envelope."""
    if "scenes" not in payload:
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

    parsed: dict[str, dict[str, Any]] = {}
    for scene_id, scene_payload in scene_payloads.items():
        if not isinstance(scene_id, str):
            raise ValueError("AI multi-scene response scene IDs must be strings.")
        if not scene_id.strip() or any(character.isspace() for character in scene_id):
            raise ValueError("AI multi-scene response scene ID cannot contain whitespace.")
        if not isinstance(scene_payload, dict):
            raise ValueError("AI multi-scene response scene payloads must be objects.")
        parsed[scene_id] = dict(scene_payload)

    return parsed


def _scene_payloads_from_list(
    scenes: list[Any],
) -> dict[str, dict[str, Any]]:
    """Return scene payloads from list-form multi-scene response data."""
    scene_payloads: dict[str, dict[str, Any]] = {}
    for item in scenes:
        if not isinstance(item, dict):
            raise ValueError("AI multi-scene response scene entries must be objects.")

        scene_id = item.get("scene_id")
        if not isinstance(scene_id, str):
            raise ValueError(
                "AI multi-scene response scene entries must include string scene_id."
            )
        if not scene_id.strip() or any(character.isspace() for character in scene_id):
            raise ValueError("AI multi-scene response scene ID cannot contain whitespace.")
        if scene_id in scene_payloads:
            raise ValueError(
                f"AI multi-scene response includes duplicate scene: {scene_id}"
            )

        scene_payload = dict(item)
        scene_payload.pop("scene_id")
        scene_payloads[scene_id] = scene_payload

    return scene_payloads


def _summary_ids(summary_buckets: Iterable[Sequence[str]]) -> tuple[str, ...]:
    """Return accepted or rejected summary IDs in stable first-seen order."""
    deduped: dict[str, None] = {}
    for bucket in summary_buckets:
        for summary_id in bucket:
            deduped.setdefault(summary_id, None)

    return tuple(deduped)


app = create_app_from_env()
