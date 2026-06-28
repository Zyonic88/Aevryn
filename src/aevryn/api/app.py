"""FastAPI application for the Aevryn Backend API."""

from __future__ import annotations

import base64
import binascii
import json
import logging
import os
import tempfile
import time
import uuid
from collections.abc import Awaitable, Callable, Iterable, Mapping, Sequence
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from aevryn.api.models import (
    ApiIndexResponse,
    ApiLink,
    ApiRouteCapability,
    AuthLoginRequest,
    AuthMeResponse,
    AuthMessageResponse,
    AuthPasswordResetCompleteRequest,
    AuthPasswordResetRequest,
    AuthPasswordResetResponse,
    AuthRegisterRequest,
    AuthSessionResponse,
    CanonPreviewRequest,
    CanonPreviewResponse,
    CapabilitiesResponse,
    CharacterPreviewRequest,
    CharacterPreviewResponse,
    CharacterProfileOutput,
    ContinuityPreviewRequest,
    ContinuityPreviewResponse,
    ContinuityRecordOutput,
    ContinuityReportOutput,
    ContinuitySceneOutput,
    EngineRunCreateRequest,
    EngineRunListResponse,
    EngineRunOutput,
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
    ImportCreateRequest,
    ImportInspectRequest,
    ImportInspectResponse,
    ImportListResponse,
    ImportOutput,
    OutputSection,
    ProductionPackOutput,
    ProjectCreateRequest,
    ProjectListResponse,
    ProjectOutput,
    ProjectOutputCanonSummary,
    ProjectOutputChapterSummary,
    ProjectOutputsPreviewRequest,
    ProjectOutputsPreviewResponse,
    ProjectOutputsResponse,
    ProjectOutputSurface,
    ProjectPreviewRequest,
    ProjectPreviewResponse,
    ProjectSettingsRequest,
    ProjectSettingsResponse,
    ProjectStatusExports,
    ProjectStatusImport,
    ProjectStatusResponse,
    ProjectStatusRun,
    ProjectStatusSnapshots,
    ProjectStatusWorker,
    ProjectWorkflowEvent,
    PromptPreviewRequest,
    PromptPreviewResponse,
    SceneMapEntry,
    ScenePreviewRequest,
    ScenePreviewResponse,
    SceneSheetOutput,
    SnapshotListResponse,
    SnapshotOutput,
    SnapshotStoreRequest,
    SourceFormat,
    SourceFormatsResponse,
    StorageHealth,
    StoryCreateRequest,
    StoryListResponse,
    StoryOutput,
    TimelinePreviewRequest,
    TimelinePreviewResponse,
    WorkerProcessRequest,
    WorkerProcessResponse,
    WorldPreviewRequest,
    WorldPreviewResponse,
    WorldSheetOutput,
)
from aevryn.auth import (
    AuthenticationError,
    AuthenticationService,
    InvalidCredentialsError,
    InvalidResetTokenError,
    InvalidSessionError,
    JsonAuthenticationStore,
    PasswordPolicyError,
)
from aevryn.export import ExportEngine
from aevryn.extraction import (
    EvidenceBoundedAIExtractor,
    OpenAIResponsesAIExtractionClient,
    SceneExtractor,
    StaticAIExtractionClient,
)
from aevryn.import_storage import FileSystemImportContentStore, ImportContentStore
from aevryn.importing import ImportedSource, SourceFileTextExtractor
from aevryn.persistence import (
    AccessDeniedError,
    DuplicateRecordError,
    EngineRunRecord,
    ExportRecord,
    ImportRecord,
    JsonProjectRepository,
    PersistenceError,
    ProjectRecord,
    ProjectRepository,
    ProjectSettingsRecord,
    RecordNotFoundError,
    SnapshotKind,
    SnapshotRecord,
    StoryRecord,
    UserRecord,
)
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
from aevryn.workers import (
    BackgroundJob,
    BackgroundJobHandler,
    BackgroundJobQueue,
    BackgroundJobService,
    BackgroundWorker,
    BackgroundWorkerRunSummary,
    DuplicateJobError,
    InMemoryJobQueue,
    ProjectImportSnapshotHandler,
)

API_VERSION = "v2"
logger = logging.getLogger(__name__)
ALLOWED_ORIGINS_ENV = "AEVRYN_API_ALLOWED_ORIGINS"
API_KEYS_ENV = "AEVRYN_API_KEYS"
PROJECT_DATABASE_PATH_ENV = "AEVRYN_PROJECT_DATABASE_PATH"
AUTH_STORE_PATH_ENV = "AEVRYN_AUTH_STORE_PATH"
IMPORT_STORAGE_PATH_ENV = "AEVRYN_IMPORT_STORAGE_PATH"
EXTRACTION_MODE_ENV = "AEVRYN_EXTRACTION_MODE"
OPENAI_API_KEY_ENV = "AEVRYN_OPENAI_API_KEY"
OPENAI_MODEL_ENV = "AEVRYN_OPENAI_MODEL"
OPENAI_ENDPOINT_ENV = "AEVRYN_OPENAI_ENDPOINT"
OPENAI_TIMEOUT_SECONDS_ENV = "AEVRYN_OPENAI_TIMEOUT_SECONDS"
OPENAI_MAX_RESPONSE_BYTES_ENV = "AEVRYN_OPENAI_MAX_RESPONSE_BYTES"
PLATFORM_ENGINE_VERSION = "aevryn_v1"
ALPHA_ACTIVE_RUN_TIMEOUT = timedelta(minutes=30)


def create_app_from_env(environ: Mapping[str, str] | None = None) -> FastAPI:
    """Create the Backend API application from deployment environment settings.

    Parameters:
        environ: Optional environment mapping. Defaults to ``os.environ``.

    Returns:
        Configured FastAPI application.

    Raises:
        ValueError: If configured CORS origins are unsafe or invalid.
    """
    active_environ = environ or os.environ
    (
        authentication_service,
        project_repository,
        background_job_queue,
        background_job_handler,
        import_content_store,
    ) = _platform_services_from_env(active_environ)
    return create_app(
        allowed_origins=_allowed_origins_from_env(active_environ),
        api_keys=_api_keys_from_env(active_environ),
        authentication_service=authentication_service,
        project_repository=project_repository,
        background_job_queue=background_job_queue,
        background_job_handler=background_job_handler,
        import_content_store=import_content_store,
    )


def create_app(
    allowed_origins: Sequence[str] = (),
    api_keys: Sequence[str] = (),
    authentication_service: AuthenticationService | None = None,
    project_repository: ProjectRepository | None = None,
    background_job_queue: BackgroundJobQueue | None = None,
    background_job_handler: BackgroundJobHandler | None = None,
    import_content_store: ImportContentStore | None = None,
) -> FastAPI:
    """Create the Aevryn Backend API application.

    Parameters:
        allowed_origins: Optional browser origins allowed by CORS middleware.
        api_keys: Optional deployment API keys that protect workflow routes.
        authentication_service: Optional Phase 4 authentication service.
        project_repository: Optional Phase 6 project storage repository.
        background_job_queue: Optional Phase 3 queue for engine run submission.
        background_job_handler: Optional Phase 3 worker handler for queued jobs.
        import_content_store: Optional storage adapter for uploaded source bytes.

    Returns:
        Configured FastAPI application.
    """
    normalized_api_keys = _normalize_api_keys(api_keys)
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
            allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
            allow_headers=["*"],
        )

    @app.middleware("http")
    async def api_identity_headers(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Attach identity headers and enforce optional workflow authentication."""
        request_id = _request_id(request)
        auth_error = _authentication_error(request, normalized_api_keys)
        response = auth_error if auth_error is not None else await call_next(request)
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
            storage=StorageHealth(
                project_storage=_adapter_status(project_repository),
                import_content_storage=_adapter_status(import_content_store),
            ),
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
        "/v2/auth/register",
        response_model=AuthSessionResponse,
        tags=["Authentication"],
        operation_id="postV2AuthRegister",
    )
    def auth_register(request: AuthRegisterRequest) -> AuthSessionResponse:
        """Register a platform user through the Authentication boundary."""
        service = _require_authentication_service(authentication_service)
        try:
            result = service.register(
                user_id=request.user_id,
                email=request.email,
                display_name=request.display_name,
                password=request.password,
                now=request.now,
            )
        except PasswordPolicyError as error:
            raise HTTPException(
                status_code=400,
                detail={"error": "password_policy_failed", "detail": str(error)},
            ) from error
        except AuthenticationError as error:
            raise HTTPException(
                status_code=400,
                detail={"error": "registration_failed", "detail": str(error)},
            ) from error
        return _auth_session_response(result.session)

    @app.post(
        "/v2/auth/login",
        response_model=AuthSessionResponse,
        tags=["Authentication"],
        operation_id="postV2AuthLogin",
    )
    def auth_login(request: AuthLoginRequest) -> AuthSessionResponse:
        """Log in a platform user through the Authentication boundary."""
        service = _require_authentication_service(authentication_service)
        try:
            session = service.login(
                email=request.email,
                password=request.password,
                now=request.now,
            )
        except InvalidCredentialsError as error:
            raise HTTPException(
                status_code=401,
                detail={"error": "invalid_credentials", "detail": str(error)},
            ) from error
        return _auth_session_response(session)

    @app.get(
        "/v2/auth/me",
        response_model=AuthMeResponse,
        tags=["Authentication"],
        operation_id="getV2AuthMe",
    )
    def auth_me(request: Request) -> AuthMeResponse:
        """Return the authenticated user for a bearer session token."""
        service = _require_authentication_service(authentication_service)
        token = _extract_bearer_token(request)
        if not token:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "session_required",
                    "detail": "A bearer session token is required.",
                },
            )
        now = request.headers.get("X-Aevryn-Now", "").strip()
        if not now:
            raise HTTPException(
                status_code=400,
                detail={"error": "missing_time", "detail": "X-Aevryn-Now is required."},
            )
        try:
            user = service.validate_session(session_token=token, now=now)
        except InvalidSessionError as error:
            raise HTTPException(
                status_code=401,
                detail={"error": "invalid_session", "detail": str(error)},
            ) from error
        return AuthMeResponse(
            user_id=user.user_id,
            email=user.email,
            display_name=user.display_name,
        )

    @app.post(
        "/v2/auth/password-reset/request",
        response_model=AuthPasswordResetResponse,
        tags=["Authentication"],
        operation_id="postV2AuthPasswordResetRequest",
    )
    def auth_password_reset_request(
        request: AuthPasswordResetRequest,
    ) -> AuthPasswordResetResponse:
        """Issue a password reset token through the Authentication boundary."""
        service = _require_authentication_service(authentication_service)
        try:
            reset = service.request_password_reset(
                email=request.email,
                reset_id=request.reset_id,
                now=request.now,
            )
        except AuthenticationError as error:
            raise HTTPException(
                status_code=400,
                detail={"error": "password_reset_request_failed", "detail": str(error)},
            ) from error
        return AuthPasswordResetResponse(
            user_id=reset.user_id,
            reset_token=reset.reset_token,
            expires_at=reset.expires_at,
        )

    @app.post(
        "/v2/auth/password-reset/complete",
        response_model=AuthMessageResponse,
        tags=["Authentication"],
        operation_id="postV2AuthPasswordResetComplete",
    )
    def auth_password_reset_complete(
        request: AuthPasswordResetCompleteRequest,
    ) -> AuthMessageResponse:
        """Complete a password reset through the Authentication boundary."""
        service = _require_authentication_service(authentication_service)
        try:
            service.complete_password_reset(
                reset_token=request.reset_token,
                new_password=request.new_password,
                now=request.now,
            )
        except PasswordPolicyError as error:
            raise HTTPException(
                status_code=400,
                detail={"error": "password_policy_failed", "detail": str(error)},
            ) from error
        except InvalidResetTokenError as error:
            raise HTTPException(
                status_code=400,
                detail={"error": "invalid_reset_token", "detail": str(error)},
            ) from error
        return AuthMessageResponse(status="password_reset_complete")

    @app.get(
        "/v2/projects",
        response_model=ProjectListResponse,
        tags=["Projects"],
        operation_id="getV2Projects",
    )
    def list_projects(request: Request) -> ProjectListResponse:
        """Return durable projects owned by the authenticated user."""
        repository = _require_project_repository(project_repository)
        user = _authenticated_user(
            request=request,
            authentication_service=authentication_service,
        )
        try:
            projects = repository.list_projects_for_user(user.user_id)
        except PersistenceError as error:
            raise _project_storage_error(error) from error
        return ProjectListResponse(
            projects=tuple(_project_output(project) for project in projects),
        )

    @app.post(
        "/v2/projects",
        response_model=ProjectOutput,
        tags=["Projects"],
        operation_id="postV2Projects",
    )
    def create_project(
        request_body: ProjectCreateRequest,
        request: Request,
    ) -> ProjectOutput:
        """Create one durable project for the authenticated user."""
        repository = _require_project_repository(project_repository)
        user = _authenticated_user(
            request=request,
            authentication_service=authentication_service,
        )
        try:
            project = ProjectRecord(
                project_id=request_body.project_id,
                owner_user_id=user.user_id,
                name=_normalized_project_name(request_body.name),
                created_at=request_body.now,
                updated_at=request_body.now,
            )
            repository.create_project(project)
        except ValueError as error:
            raise HTTPException(
                status_code=400,
                detail={"error": "project_create_failed", "detail": str(error)},
            ) from error
        except DuplicateRecordError as error:
            raise HTTPException(
                status_code=409,
                detail={"error": "project_exists", "detail": str(error)},
            ) from error
        except PersistenceError as error:
            raise _project_storage_error(error) from error
        return _project_output(project)

    @app.get(
        "/v2/projects/{project_id}",
        response_model=ProjectOutput,
        tags=["Projects"],
        operation_id="getV2Project",
    )
    def get_project(project_id: str, request: Request) -> ProjectOutput:
        """Return one durable project inside the authenticated user's boundary."""
        repository = _require_project_repository(project_repository)
        user = _authenticated_user(
            request=request,
            authentication_service=authentication_service,
        )
        try:
            return _project_output(
                repository.get_project(user_id=user.user_id, project_id=project_id)
            )
        except (AccessDeniedError, RecordNotFoundError) as error:
            raise HTTPException(
                status_code=404,
                detail={"error": "project_not_found", "detail": "Project not found."},
            ) from error
        except PersistenceError as error:
            raise _project_storage_error(error) from error

    @app.get(
        "/v2/projects/{project_id}/settings",
        response_model=ProjectSettingsResponse,
        tags=["Projects"],
        operation_id="getV2ProjectSettings",
    )
    def get_project_settings(project_id: str, request: Request) -> ProjectSettingsResponse:
        """Return durable settings inside the authenticated user's project boundary."""
        repository = _require_project_repository(project_repository)
        user = _authenticated_user(
            request=request,
            authentication_service=authentication_service,
        )
        try:
            return _project_settings_output(
                repository.get_project_settings(user_id=user.user_id, project_id=project_id)
            )
        except (AccessDeniedError, RecordNotFoundError) as error:
            raise HTTPException(
                status_code=404,
                detail={"error": "project_not_found", "detail": "Project not found."},
            ) from error
        except PersistenceError as error:
            raise _project_storage_error(error) from error

    @app.put(
        "/v2/projects/{project_id}/settings",
        response_model=ProjectSettingsResponse,
        tags=["Projects"],
        operation_id="putV2ProjectSettings",
    )
    def update_project_settings(
        project_id: str,
        request_body: ProjectSettingsRequest,
        request: Request,
    ) -> ProjectSettingsResponse:
        """Update durable settings inside the authenticated user's project boundary."""
        repository = _require_project_repository(project_repository)
        user = _authenticated_user(
            request=request,
            authentication_service=authentication_service,
        )
        try:
            repository.get_project(user_id=user.user_id, project_id=project_id)
            settings = ProjectSettingsRecord(
                project_id=project_id,
                default_export_format=_normalized_machine_token(
                    request_body.default_export_format,
                    "Default export format",
                ),
                locale=_normalized_locale(request_body.locale),
            )
            repository.save_project_settings(settings)
        except (AccessDeniedError, RecordNotFoundError) as error:
            raise HTTPException(
                status_code=404,
                detail={"error": "project_not_found", "detail": "Project not found."},
            ) from error
        except ValueError as error:
            raise HTTPException(
                status_code=400,
                detail={"error": "project_settings_failed", "detail": str(error)},
            ) from error
        except PersistenceError as error:
            raise _project_storage_error(error) from error
        return _project_settings_output(settings)

    @app.get(
        "/v2/projects/{project_id}/stories",
        response_model=StoryListResponse,
        tags=["Projects"],
        operation_id="getV2ProjectStories",
    )
    def list_project_stories(project_id: str, request: Request) -> StoryListResponse:
        """Return durable story metadata inside the authenticated project boundary."""
        repository = _require_project_repository(project_repository)
        user = _authenticated_user(
            request=request,
            authentication_service=authentication_service,
        )
        try:
            stories = repository.list_stories_for_project(
                user_id=user.user_id,
                project_id=project_id,
            )
        except (AccessDeniedError, RecordNotFoundError) as error:
            raise HTTPException(
                status_code=404,
                detail={"error": "project_not_found", "detail": "Project not found."},
            ) from error
        except PersistenceError as error:
            raise _project_storage_error(error) from error
        return StoryListResponse(stories=tuple(_story_output(story) for story in stories))

    @app.get(
        "/v2/projects/{project_id}/snapshots",
        response_model=SnapshotListResponse,
        tags=["Projects"],
        operation_id="getV2ProjectSnapshots",
    )
    def list_project_snapshots(project_id: str, request: Request) -> SnapshotListResponse:
        """Return persisted engine output snapshots inside an authenticated project."""
        repository = _require_project_repository(project_repository)
        user = _authenticated_user(
            request=request,
            authentication_service=authentication_service,
        )
        try:
            snapshots = repository.list_snapshots_for_project(
                user_id=user.user_id,
                project_id=project_id,
            )
        except (AccessDeniedError, RecordNotFoundError) as error:
            raise HTTPException(
                status_code=404,
                detail={"error": "project_not_found", "detail": "Project not found."},
            ) from error
        except PersistenceError as error:
            raise _project_storage_error(error) from error
        return SnapshotListResponse(
            snapshots=tuple(_snapshot_output(snapshot) for snapshot in snapshots),
        )

    @app.get(
        "/v2/projects/{project_id}/outputs",
        response_model=ProjectOutputsResponse,
        tags=["Projects"],
        operation_id="getV2ProjectOutputs",
    )
    def project_outputs(project_id: str, request: Request) -> ProjectOutputsResponse:
        """Return API-owned processed output summaries for alpha workspace surfaces."""
        repository = _require_project_repository(project_repository)
        user = _authenticated_user(
            request=request,
            authentication_service=authentication_service,
        )
        try:
            stories = repository.list_stories_for_project(
                user_id=user.user_id,
                project_id=project_id,
            )
            imports = tuple(
                import_record
                for story in stories
                for import_record in repository.list_imports_for_story(
                    user_id=user.user_id,
                    story_id=story.story_id,
                )
            )
            runs = repository.list_engine_runs_for_project(
                user_id=user.user_id,
                project_id=project_id,
            )
            snapshots = repository.list_snapshots_for_project(
                user_id=user.user_id,
                project_id=project_id,
            )
        except (AccessDeniedError, RecordNotFoundError) as error:
            raise HTTPException(
                status_code=404,
                detail={"error": "project_not_found", "detail": "Project not found."},
            ) from error
        except PersistenceError as error:
            raise _project_storage_error(error) from error
        return _project_outputs_response(
            project_id=project_id,
            imports=imports,
            runs=runs,
            snapshots=snapshots,
        )

    @app.post(
        "/v2/projects/{project_id}/stories",
        response_model=StoryOutput,
        tags=["Projects"],
        operation_id="postV2ProjectStories",
    )
    def create_project_story(
        project_id: str,
        request_body: StoryCreateRequest,
        request: Request,
    ) -> StoryOutput:
        """Create durable story metadata inside the authenticated project boundary."""
        repository = _require_project_repository(project_repository)
        user = _authenticated_user(
            request=request,
            authentication_service=authentication_service,
        )
        try:
            repository.get_project(user_id=user.user_id, project_id=project_id)
            story = StoryRecord(
                story_id=request_body.story_id,
                project_id=project_id,
                title=_normalized_story_title(request_body.title),
                created_at=request_body.now,
                updated_at=request_body.now,
            )
            repository.create_story(story)
        except (AccessDeniedError, RecordNotFoundError) as error:
            raise HTTPException(
                status_code=404,
                detail={"error": "project_not_found", "detail": "Project not found."},
            ) from error
        except DuplicateRecordError as error:
            raise HTTPException(
                status_code=409,
                detail={"error": "story_exists", "detail": str(error)},
            ) from error
        except ValueError as error:
            raise HTTPException(
                status_code=400,
                detail={"error": "story_create_failed", "detail": str(error)},
            ) from error
        except PersistenceError as error:
            raise _project_storage_error(error) from error
        return _story_output(story)

    @app.delete(
        "/v2/projects/{project_id}/stories/{story_id}",
        status_code=204,
        tags=["Projects"],
        operation_id="deleteV2ProjectStory",
    )
    def delete_project_story(project_id: str, story_id: str, request: Request) -> Response:
        """Hard-delete a story and all stored metadata/content scoped to it."""
        repository = _require_project_repository(project_repository)
        user = _authenticated_user(
            request=request,
            authentication_service=authentication_service,
        )
        try:
            _require_story_scope(
                repository=repository,
                user_id=user.user_id,
                project_id=project_id,
                story_id=story_id,
            )
            deleted_imports = repository.delete_story(user_id=user.user_id, story_id=story_id)
            if import_content_store is not None:
                for import_record in deleted_imports:
                    import_content_store.delete_import_content(import_record.storage_ref)
        except (AccessDeniedError, RecordNotFoundError, ValueError) as error:
            raise HTTPException(
                status_code=404,
                detail={"error": "story_not_found", "detail": "Story not found."},
            ) from error
        except PersistenceError as error:
            raise _project_storage_error(error) from error
        return Response(status_code=204)

    @app.get(
        "/v2/projects/{project_id}/stories/{story_id}/snapshots",
        response_model=SnapshotListResponse,
        tags=["Projects"],
        operation_id="getV2StorySnapshots",
    )
    def list_story_snapshots(
        project_id: str,
        story_id: str,
        request: Request,
        snapshot_kind: str | None = Query(default=None),
    ) -> SnapshotListResponse:
        """Return persisted engine output snapshots inside an authenticated story."""
        repository = _require_project_repository(project_repository)
        user = _authenticated_user(
            request=request,
            authentication_service=authentication_service,
        )
        try:
            _require_story_scope(
                repository=repository,
                user_id=user.user_id,
                project_id=project_id,
                story_id=story_id,
            )
            snapshots = repository.list_snapshots_for_story(
                user_id=user.user_id,
                story_id=story_id,
                snapshot_kind=_snapshot_kind_filter(snapshot_kind),
            )
        except (AccessDeniedError, RecordNotFoundError, ValueError) as error:
            raise HTTPException(
                status_code=404,
                detail={"error": "story_not_found", "detail": "Story not found."},
            ) from error
        except PersistenceError as error:
            raise _project_storage_error(error) from error
        return SnapshotListResponse(
            snapshots=tuple(_snapshot_output(snapshot) for snapshot in snapshots),
        )

    @app.get(
        "/v2/projects/{project_id}/stories/{story_id}/imports",
        response_model=ImportListResponse,
        tags=["Projects"],
        operation_id="getV2StoryImports",
    )
    def list_story_imports(
        project_id: str,
        story_id: str,
        request: Request,
    ) -> ImportListResponse:
        """Return durable import metadata inside the authenticated story boundary."""
        repository = _require_project_repository(project_repository)
        user = _authenticated_user(
            request=request,
            authentication_service=authentication_service,
        )
        try:
            _require_story_scope(
                repository=repository,
                user_id=user.user_id,
                project_id=project_id,
                story_id=story_id,
            )
            imports = repository.list_imports_for_story(
                user_id=user.user_id,
                story_id=story_id,
            )
        except (AccessDeniedError, RecordNotFoundError, ValueError) as error:
            raise HTTPException(
                status_code=404,
                detail={"error": "story_not_found", "detail": "Story not found."},
            ) from error
        except PersistenceError as error:
            raise _project_storage_error(error) from error
        return ImportListResponse(
            imports=tuple(_import_output(import_record) for import_record in imports),
        )

    @app.post(
        "/v2/projects/{project_id}/stories/{story_id}/imports",
        response_model=ImportOutput,
        tags=["Projects"],
        operation_id="postV2StoryImports",
    )
    def create_story_import(
        project_id: str,
        story_id: str,
        request_body: ImportCreateRequest,
        request: Request,
    ) -> ImportOutput:
        """Inspect and persist source import metadata inside a story boundary."""
        repository = _require_project_repository(project_repository)
        user = _authenticated_user(
            request=request,
            authentication_service=authentication_service,
        )
        try:
            _require_story_scope(
                repository=repository,
                user_id=user.user_id,
                project_id=project_id,
                story_id=story_id,
            )
        except (AccessDeniedError, RecordNotFoundError, ValueError) as error:
            raise HTTPException(
                status_code=404,
                detail={"error": "story_not_found", "detail": "Story not found."},
            ) from error
        try:
            imported_source, source_format = _import_request_source(request_body)
            import_record = _import_record(
                request=request_body,
                story_id=story_id,
                source_format=source_format,
                imported_source=imported_source,
            )
            if import_content_store is not None:
                import_content_store.store_import_content(
                    import_record.storage_ref,
                    _decode_base64(request_body.content_base64),
                )
            repository.record_import(import_record)
        except DuplicateRecordError as error:
            raise HTTPException(
                status_code=409,
                detail={"error": "import_exists", "detail": str(error)},
            ) from error
        except ValueError as error:
            raise HTTPException(
                status_code=400,
                detail={"error": "import_create_failed", "detail": str(error)},
            ) from error
        except PersistenceError as error:
            raise _project_storage_error(error) from error
        return _import_output(import_record)

    @app.get(
        "/v2/projects/{project_id}/runs",
        response_model=EngineRunListResponse,
        tags=["Projects"],
        operation_id="getV2ProjectRuns",
    )
    def list_project_runs(project_id: str, request: Request) -> EngineRunListResponse:
        """Return durable engine run metadata inside the authenticated project boundary."""
        repository = _require_project_repository(project_repository)
        user = _authenticated_user(
            request=request,
            authentication_service=authentication_service,
        )
        try:
            _reconcile_orphaned_project_runs(
                repository=repository,
                background_job_queue=background_job_queue,
                user_id=user.user_id,
                project_id=project_id,
            )
            runs = repository.list_engine_runs_for_project(
                user_id=user.user_id,
                project_id=project_id,
            )
        except (AccessDeniedError, RecordNotFoundError) as error:
            raise HTTPException(
                status_code=404,
                detail={"error": "project_not_found", "detail": "Project not found."},
            ) from error
        except PersistenceError as error:
            raise _project_storage_error(error) from error
        return EngineRunListResponse(runs=tuple(_engine_run_output(run) for run in runs))

    @app.get(
        "/v2/projects/{project_id}/status",
        response_model=ProjectStatusResponse,
        tags=["Projects"],
        operation_id="getV2ProjectStatus",
    )
    def project_status(project_id: str, request: Request) -> ProjectStatusResponse:
        """Return metadata-only project status for monitoring surfaces."""
        started_at = time.perf_counter()
        repository = _require_project_repository(project_repository)
        user = _authenticated_user(
            request=request,
            authentication_service=authentication_service,
        )
        try:
            _reconcile_orphaned_project_runs(
                repository=repository,
                background_job_queue=background_job_queue,
                user_id=user.user_id,
                project_id=project_id,
            )
            stories = repository.list_stories_for_project(
                user_id=user.user_id,
                project_id=project_id,
            )
            imports = tuple(
                import_record
                for story in stories
                for import_record in repository.list_imports_for_story(
                    user_id=user.user_id,
                    story_id=story.story_id,
                )
            )
            runs = repository.list_engine_runs_for_project(
                user_id=user.user_id,
                project_id=project_id,
            )
            snapshots = repository.list_snapshots_for_project(
                user_id=user.user_id,
                project_id=project_id,
            )
            exports = repository.list_exports_for_project(
                user_id=user.user_id,
                project_id=project_id,
            )
        except (AccessDeniedError, RecordNotFoundError) as error:
            raise HTTPException(
                status_code=404,
                detail={"error": "project_not_found", "detail": "Project not found."},
            ) from error
        except PersistenceError as error:
            raise _project_storage_error(error) from error
        response = _project_status_output(
            project_id=project_id,
            story_count=len(stories),
            imports=imports,
            runs=runs,
            snapshots=snapshots,
            exports=exports,
            background_job_queue=background_job_queue,
        )
        logger.info(
            "api_workflow_succeeded",
            extra={
                "workflow_kind": "project_status",
                "workflow_status": "succeeded",
                "duration_ms": _elapsed_ms(started_at),
                "project_id": project_id,
                "project_status": response.status,
                "story_count": response.story_count,
                "import_count": response.import_count,
                "run_count": response.run_count,
                "snapshot_count": response.snapshots.count,
                "export_count": response.exports.count,
                "worker_state": response.worker.state,
            },
        )
        return response

    @app.post(
        "/v2/projects/{project_id}/stories/{story_id}/imports/{import_id}/runs",
        response_model=EngineRunOutput,
        tags=["Projects"],
        operation_id="postV2ImportRuns",
    )
    def submit_import_run(
        project_id: str,
        story_id: str,
        import_id: str,
        request_body: EngineRunCreateRequest,
        request: Request,
    ) -> EngineRunOutput:
        """Submit a saved import for durable background engine processing."""
        repository = _require_project_repository(project_repository)
        queue = _require_background_job_queue(background_job_queue)
        user = _authenticated_user(
            request=request,
            authentication_service=authentication_service,
        )
        try:
            _require_import_scope(
                repository=repository,
                user_id=user.user_id,
                project_id=project_id,
                story_id=story_id,
                import_id=import_id,
            )
        except (AccessDeniedError, RecordNotFoundError, ValueError) as error:
            raise HTTPException(
                status_code=404,
                detail={"error": "import_not_found", "detail": "Import not found."},
            ) from error
        try:
            existing_runs = repository.list_engine_runs_for_project(
                user_id=user.user_id,
                project_id=project_id,
            )
            existing_run = _active_or_completed_import_run(
                runs=existing_runs,
                import_id=import_id,
            )
            if existing_run is not None:
                if _run_is_stale(existing_run, request_body.now):
                    repository.update_engine_run(
                        replace(
                            existing_run,
                            status="failed",
                            status_updated_at=request_body.now,
                            finished_at=request_body.now,
                            error_summary="Processing timed out before completion.",
                        )
                    )
                else:
                    raise HTTPException(
                        status_code=409,
                        detail={
                            "error": "import_run_already_active",
                            "detail": _import_run_already_active_detail(existing_run),
                        },
                    )
            BackgroundJobService(
                repository=repository,
                queue=queue,
                engine_version=PLATFORM_ENGINE_VERSION,
            ).submit_import_processing_job(
                job_id=request_body.job_id,
                run_id=request_body.run_id,
                project_id=project_id,
                story_id=story_id,
                import_id=import_id,
                queued_at=request_body.now,
            )
            run = repository.get_engine_run(user_id=user.user_id, run_id=request_body.run_id)
        except HTTPException:
            raise
        except (DuplicateRecordError, DuplicateJobError) as error:
            raise HTTPException(
                status_code=409,
                detail={"error": "run_exists", "detail": str(error)},
            ) from error
        except ValueError as error:
            raise HTTPException(
                status_code=400,
                detail={"error": "run_create_failed", "detail": str(error)},
            ) from error
        except PersistenceError as error:
            raise _project_storage_error(error) from error
        return _engine_run_output(run)

    @app.post(
        "/v2/workers/process",
        response_model=WorkerProcessResponse,
        tags=["Workers"],
        operation_id="postV2WorkersProcess",
    )
    def process_worker_jobs(request_body: WorkerProcessRequest) -> WorkerProcessResponse:
        """Drain queued background jobs through the worker boundary."""
        repository = _require_project_repository(project_repository)
        queue = _require_background_job_queue(background_job_queue)
        handler = _require_background_job_handler(background_job_handler)
        try:
            summary = BackgroundWorker(
                repository=repository,
                queue=queue,
                handler=handler,
            ).process_available(
                started_at=request_body.started_at,
                finished_at=request_body.finished_at,
                max_jobs=request_body.max_jobs,
            )
        except ValueError as error:
            raise HTTPException(
                status_code=400,
                detail={"error": "worker_process_failed", "detail": str(error)},
            ) from error
        except PersistenceError as error:
            raise _project_storage_error(error) from error
        return _worker_process_response(summary)

    @app.post(
        "/v2/workers/runs/{run_id}/snapshots",
        response_model=SnapshotOutput,
        tags=["Workers"],
        operation_id="postV2WorkerRunSnapshots",
    )
    def store_worker_run_snapshot(
        run_id: str,
        request_body: SnapshotStoreRequest,
    ) -> SnapshotOutput:
        """Persist one trusted worker-produced snapshot for a completed run."""
        repository = _require_project_repository(project_repository)
        try:
            run = repository.get_engine_run_for_worker(run_id=run_id)
            snapshot = SnapshotRecord(
                snapshot_id=request_body.snapshot_id,
                project_id=run.project_id,
                story_id=run.story_id,
                run_id=run.run_id,
                snapshot_kind=_required_snapshot_kind(request_body.snapshot_kind),
                content_type=request_body.content_type,
                serialized_output=request_body.serialized_output,
                created_at=request_body.now,
            )
            repository.store_snapshot(snapshot)
        except RecordNotFoundError as error:
            raise HTTPException(
                status_code=404,
                detail={"error": "run_not_found", "detail": "Run not found."},
            ) from error
        except DuplicateRecordError as error:
            raise HTTPException(
                status_code=409,
                detail={"error": "snapshot_exists", "detail": str(error)},
            ) from error
        except ValueError as error:
            raise HTTPException(
                status_code=400,
                detail={"error": "snapshot_store_failed", "detail": str(error)},
            ) from error
        except PersistenceError as error:
            raise _project_storage_error(error) from error
        return _snapshot_output(snapshot)

    @app.post(
        "/v2/imports/inspect",
        response_model=ImportInspectResponse,
        tags=["Import"],
        operation_id="postV2ImportsInspect",
    )
    def inspect_import(request: ImportInspectRequest) -> ImportInspectResponse:
        """Inspect source structure through Project Manager and Story Import."""
        started_at = time.perf_counter()
        imported_source, source_format = _import_request_source(request)
        response = _import_response(
            source_format=source_format,
            imported_source=imported_source,
        )
        logger.info(
            "api_workflow_succeeded",
            extra={
                **_workflow_request_extra(
                    kind="import_inspect",
                    request=request,
                    status="succeeded",
                    source_format=source_format,
                ),
                "duration_ms": _elapsed_ms(started_at),
                "scene_count": response.scenes,
                "evidence_anchor_count": response.evidence_anchors,
            },
        )
        return response

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
            _log_workflow_failed(
                kind="extraction_prompt",
                request=request,
                error_code="extraction_prompt_failed",
                error=error,
            )
            raise HTTPException(
                status_code=400,
                detail={"error": "extraction_prompt_failed", "detail": str(error)},
            ) from error

        prompt = EvidenceBoundedAIExtractor(
            client=StaticAIExtractionClient("{}")
        ).build_prompt(extraction_input)
        logger.info(
            "api_workflow_succeeded",
            extra={
                **_workflow_request_extra(
                    kind="extraction_prompt",
                    request=request,
                    status="succeeded",
                    source_format=source_format,
                ),
                "evidence_anchor_count": len(extraction_input.evidence_anchor_ids),
                "scene_id": extraction_input.scene_id,
            },
        )
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
            result, _source_format = _run_logged_project_result(
                kind="extraction_apply",
                request=request,
                error_code="extraction_apply_failed",
            )
        except ValueError as error:
            raise HTTPException(
                status_code=400,
                detail={"error": "extraction_apply_failed", "detail": str(error)},
            ) from error

        return _extraction_apply_response(result)

    @app.post(
        "/v2/canon/preview",
        response_model=CanonPreviewResponse,
        tags=["Canon"],
        operation_id="postV2CanonPreview",
    )
    def preview_canon(request: CanonPreviewRequest) -> CanonPreviewResponse:
        """Preview accepted Canon metadata through the Canon API."""
        try:
            result, source_format = _run_logged_project_result(
                kind="canon_preview",
                request=request,
                error_code="canon_preview_failed",
            )
            return _canon_preview_response(result=result, source_format=source_format)
        except ValueError as error:
            raise HTTPException(
                status_code=400,
                detail={"error": "canon_preview_failed", "detail": str(error)},
            ) from error

    @app.post(
        "/v2/timeline/preview",
        response_model=TimelinePreviewResponse,
        tags=["Timeline"],
        operation_id="postV2TimelinePreview",
    )
    def preview_timeline(request: TimelinePreviewRequest) -> TimelinePreviewResponse:
        """Preview Timeline metadata through the Timeline API."""
        try:
            result, source_format = _run_logged_project_result(
                kind="timeline_preview",
                request=request,
                error_code="timeline_preview_failed",
            )
            return _timeline_preview_response(result=result, source_format=source_format)
        except ValueError as error:
            raise HTTPException(
                status_code=400,
                detail={"error": "timeline_preview_failed", "detail": str(error)},
            ) from error

    @app.post(
        "/v2/projects/preview",
        response_model=ProjectPreviewResponse,
        tags=["Projects"],
        operation_id="postV2ProjectsPreview",
    )
    def preview_project(request: ProjectPreviewRequest) -> ProjectPreviewResponse:
        """Preview stateless project metadata through Project Manager."""
        try:
            result, source_format = _run_logged_project_result(
                kind="project_preview",
                request=request,
                error_code="project_preview_failed",
            )
            return _project_preview_response(
                result=result,
                source_format=source_format,
            )
        except ValueError as error:
            raise HTTPException(
                status_code=400,
                detail={"error": "project_preview_failed", "detail": str(error)},
            ) from error

    @app.post(
        "/v2/characters/preview",
        response_model=CharacterPreviewResponse,
        tags=["Characters"],
        operation_id="postV2CharactersPreview",
    )
    def preview_characters(request: CharacterPreviewRequest) -> CharacterPreviewResponse:
        """Preview character profiles through the Character API."""
        try:
            result, source_format = _run_logged_project_result(
                kind="character_preview",
                request=request,
                error_code="character_preview_failed",
            )
            return _character_preview_response(
                request=request,
                result=result,
                source_format=source_format,
            )
        except ValueError as error:
            raise HTTPException(
                status_code=400,
                detail={"error": "character_preview_failed", "detail": str(error)},
            ) from error

    @app.post(
        "/v2/scenes/preview",
        response_model=ScenePreviewResponse,
        tags=["Scenes"],
        operation_id="postV2ScenesPreview",
    )
    def preview_scene(request: ScenePreviewRequest) -> ScenePreviewResponse:
        """Preview a scene sheet through the Scene API."""
        try:
            result, source_format = _run_logged_project_result(
                kind="scene_preview",
                request=request,
                error_code="scene_preview_failed",
            )
            return _scene_preview_response(
                request=request,
                result=result,
                source_format=source_format,
            )
        except ValueError as error:
            raise HTTPException(
                status_code=400,
                detail={"error": "scene_preview_failed", "detail": str(error)},
            ) from error

    @app.post(
        "/v2/prompts/preview",
        response_model=PromptPreviewResponse,
        tags=["Prompts"],
        operation_id="postV2PromptsPreview",
    )
    def preview_prompt(request: PromptPreviewRequest) -> PromptPreviewResponse:
        """Preview a production pack through the Prompt API."""
        try:
            result, source_format = _run_logged_project_result(
                kind="prompt_preview",
                request=request,
                error_code="prompt_preview_failed",
            )
            return _prompt_preview_response(
                request=request,
                result=result,
                source_format=source_format,
            )
        except ValueError as error:
            raise HTTPException(
                status_code=400,
                detail={"error": "prompt_preview_failed", "detail": str(error)},
            ) from error

    @app.post(
        "/v2/world/preview",
        response_model=WorldPreviewResponse,
        tags=["World"],
        operation_id="postV2WorldPreview",
    )
    def preview_world(request: WorldPreviewRequest) -> WorldPreviewResponse:
        """Preview world state through the World API."""
        try:
            result, source_format = _run_logged_project_result(
                kind="world_preview",
                request=request,
                error_code="world_preview_failed",
            )
            return _world_preview_response(
                request=request,
                result=result,
                source_format=source_format,
            )
        except ValueError as error:
            raise HTTPException(
                status_code=400,
                detail={"error": "world_preview_failed", "detail": str(error)},
            ) from error

    @app.post(
        "/v2/continuity/preview",
        response_model=ContinuityPreviewResponse,
        tags=["Continuity"],
        operation_id="postV2ContinuityPreview",
    )
    def preview_continuity(
        request: ContinuityPreviewRequest,
    ) -> ContinuityPreviewResponse:
        """Preview continuity changes through the Continuity API."""
        try:
            result, source_format = _run_logged_project_result(
                kind="continuity_preview",
                request=request,
                error_code="continuity_preview_failed",
            )
            return _continuity_preview_response(
                result=result,
                source_format=source_format,
            )
        except ValueError as error:
            raise HTTPException(
                status_code=400,
                detail={"error": "continuity_preview_failed", "detail": str(error)},
            ) from error

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
            result, source_format = _run_logged_project_result(
                kind="project_outputs_preview",
                request=request,
                error_code="project_output_preview_failed",
            )
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
            result, source_format = _run_logged_project_result(
                kind="export_preview",
                request=request,
                error_code="export_preview_failed",
            )
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


def _adapter_status(adapter: object | None) -> str:
    """Return a metadata-only configured/unconfigured storage status."""
    return "configured" if adapter is not None else "unconfigured"


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


def _api_keys_from_env(environ: Mapping[str, str]) -> tuple[str, ...]:
    """Return workflow API keys from deployment environment settings."""
    return _normalize_api_keys(environ.get(API_KEYS_ENV, "").split(","))


def _platform_services_from_env(
    environ: Mapping[str, str],
) -> tuple[
    AuthenticationService | None,
    ProjectRepository | None,
    BackgroundJobQueue | None,
    BackgroundJobHandler | None,
    ImportContentStore | None,
]:
    """Return configured platform services from deployment environment settings."""
    database_path = environ.get(PROJECT_DATABASE_PATH_ENV, "").strip()
    if not database_path:
        return None, None, None, None, None

    project_database_path = Path(database_path)
    repository = JsonProjectRepository(project_database_path)
    import_content_store = FileSystemImportContentStore(
        _import_storage_path_from_env(environ, project_database_path)
    )
    auth_store = JsonAuthenticationStore(
        _auth_store_path_from_env(environ, project_database_path)
    )
    authentication_service = AuthenticationService(
        repository=repository,
        credential_store=auth_store,
        session_store=auth_store,
    )
    return (
        authentication_service,
        repository,
        InMemoryJobQueue(),
        ProjectImportSnapshotHandler(
            repository,
            import_content_store,
            extractor=_worker_extractor_from_env(environ),
        ),
        import_content_store,
    )


def _worker_extractor_from_env(environ: Mapping[str, str]) -> SceneExtractor | None:
    """Return the configured worker extractor, or None for local demo mode."""
    mode = environ.get(EXTRACTION_MODE_ENV, "").strip().lower()
    if mode in {"", "demo"}:
        return None
    if mode != "openai":
        raise ValueError("AEVRYN_EXTRACTION_MODE must be 'demo' or 'openai'.")

    api_key = environ.get(OPENAI_API_KEY_ENV, "").strip()
    if not api_key:
        raise ValueError("AEVRYN_OPENAI_API_KEY is required for openai extraction.")
    model = environ.get(OPENAI_MODEL_ENV, "").strip()
    if not model:
        raise ValueError("AEVRYN_OPENAI_MODEL is required for openai extraction.")

    return EvidenceBoundedAIExtractor(
        OpenAIResponsesAIExtractionClient(
            api_key=api_key,
            model=model,
            endpoint=_optional_env_text(environ, OPENAI_ENDPOINT_ENV)
            or "https://api.openai.com/v1/responses",
            timeout_seconds=_optional_positive_float(
                environ,
                OPENAI_TIMEOUT_SECONDS_ENV,
                default=30.0,
            ),
            max_response_bytes=_optional_positive_int(
                environ,
                OPENAI_MAX_RESPONSE_BYTES_ENV,
                default=1_048_576,
            ),
        )
    )


def _auth_store_path_from_env(
    environ: Mapping[str, str],
    project_database_path: Path,
) -> Path:
    """Return the local authentication store path for environment app wiring."""
    configured_path = environ.get(AUTH_STORE_PATH_ENV, "").strip()
    if configured_path:
        return Path(configured_path)
    return project_database_path.with_name(f"{project_database_path.stem}_auth.json")


def _import_storage_path_from_env(
    environ: Mapping[str, str],
    project_database_path: Path,
) -> Path:
    """Return the local import content storage directory for environment app wiring."""
    configured_path = environ.get(IMPORT_STORAGE_PATH_ENV, "").strip()
    if configured_path:
        return Path(configured_path)
    return project_database_path.with_name(f"{project_database_path.stem}_imports")


def _optional_env_text(environ: Mapping[str, str], key: str) -> str:
    """Return an optional nonblank environment value."""
    return environ.get(key, "").strip()


def _optional_positive_float(
    environ: Mapping[str, str],
    key: str,
    *,
    default: float,
) -> float:
    """Return a positive float environment value or a default."""
    raw_value = environ.get(key, "").strip()
    if not raw_value:
        return default
    try:
        value = float(raw_value)
    except ValueError as error:
        raise ValueError(f"{key} must be a positive number.") from error
    if value <= 0:
        raise ValueError(f"{key} must be a positive number.")
    return value


def _optional_positive_int(
    environ: Mapping[str, str],
    key: str,
    *,
    default: int,
) -> int:
    """Return a positive integer environment value or a default."""
    raw_value = environ.get(key, "").strip()
    if not raw_value:
        return default
    try:
        value = int(raw_value)
    except ValueError as error:
        raise ValueError(f"{key} must be a positive integer.") from error
    if value <= 0:
        raise ValueError(f"{key} must be a positive integer.")
    return value


def _normalize_api_keys(api_keys: Sequence[str]) -> tuple[str, ...]:
    """Return stable nonblank API keys or reject invalid key configuration."""
    normalized = tuple(key.strip() for key in api_keys if key.strip())
    if len(normalized) != len(set(normalized)):
        raise ValueError("AEVRYN_API_KEYS cannot contain duplicate keys.")

    return normalized


def _authentication_error(
    request: Request,
    api_keys: Sequence[str],
) -> JSONResponse | None:
    """Return an authentication error for protected routes when configured."""
    if not api_keys or not _is_auth_protected_route(request):
        return None

    provided_key = _extract_api_key(request)
    if not provided_key:
        return JSONResponse(
            status_code=401,
            content=ErrorResponse(
                error="authentication_required",
                detail="A valid API key is required for this workflow route.",
            ).model_dump(),
        )
    if provided_key not in api_keys:
        return JSONResponse(
            status_code=403,
            content=ErrorResponse(
                error="invalid_api_key",
                detail="The provided API key is not authorized.",
            ).model_dump(),
        )

    return None


def _is_auth_protected_route(request: Request) -> bool:
    """Return whether a request touches a Phase 1 workflow route."""
    path = request.url.path
    if path.startswith("/v2/auth/"):
        return False
    if path == "/v2/projects" or (
        path.startswith("/v2/projects/") and path != "/v2/projects/preview"
    ):
        return False
    return request.method.upper() == "POST" and path.startswith("/v2/")


def _extract_api_key(request: Request) -> str:
    """Return an API key from supported request headers."""
    explicit_key = request.headers.get("X-Aevryn-API-Key", "").strip()
    if explicit_key:
        return explicit_key

    authorization = request.headers.get("Authorization", "").strip()
    scheme, separator, token = authorization.partition(" ")
    if separator and scheme.lower() == "bearer":
        return token.strip()

    return ""


def _require_authentication_service(
    authentication_service: AuthenticationService | None,
) -> AuthenticationService:
    """Return the configured Authentication service or fail clearly."""
    if authentication_service is None:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "authentication_unavailable",
                "detail": "Authentication service is not configured.",
            },
        )
    return authentication_service


def _require_project_repository(
    project_repository: ProjectRepository | None,
) -> ProjectRepository:
    """Return the configured Project Repository or fail clearly."""
    if project_repository is None:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "project_storage_unavailable",
                "detail": "Project storage is not configured.",
            },
        )
    return project_repository


def _require_background_job_queue(
    background_job_queue: BackgroundJobQueue | None,
) -> BackgroundJobQueue:
    """Return the configured background queue or fail clearly."""
    if background_job_queue is None:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "background_queue_unavailable",
                "detail": "Background job queue is not configured.",
            },
        )
    return background_job_queue


def _require_background_job_handler(
    background_job_handler: BackgroundJobHandler | None,
) -> BackgroundJobHandler:
    """Return the configured background handler or fail clearly."""
    if background_job_handler is None:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "background_worker_unavailable",
                "detail": "Background worker handler is not configured.",
            },
        )
    return background_job_handler


def _authenticated_user(
    request: Request,
    authentication_service: AuthenticationService | None,
) -> UserRecord:
    """Return the authenticated user for project storage routes."""
    service = _require_authentication_service(authentication_service)
    token = _extract_bearer_token(request)
    if not token:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "session_required",
                "detail": "A bearer session token is required.",
            },
        )
    now = request.headers.get("X-Aevryn-Now", "").strip()
    if not now:
        raise HTTPException(
            status_code=400,
            detail={"error": "missing_time", "detail": "X-Aevryn-Now is required."},
        )
    try:
        return service.validate_session(session_token=token, now=now)
    except InvalidSessionError as error:
        raise HTTPException(
            status_code=401,
            detail={"error": "invalid_session", "detail": str(error)},
        ) from error


def _project_output(project: ProjectRecord) -> ProjectOutput:
    """Convert persisted project metadata to the API contract."""
    return ProjectOutput(
        project_id=project.project_id,
        name=project.name,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


def _project_settings_output(settings: ProjectSettingsRecord) -> ProjectSettingsResponse:
    """Convert persisted project settings to the API contract."""
    return ProjectSettingsResponse(
        project_id=settings.project_id,
        default_export_format=settings.default_export_format,
        locale=settings.locale,
    )


def _story_output(story: StoryRecord) -> StoryOutput:
    """Convert persisted story metadata to the API contract."""
    return StoryOutput(
        story_id=story.story_id,
        project_id=story.project_id,
        title=story.title,
        created_at=story.created_at,
        updated_at=story.updated_at,
    )


def _import_output(import_record: ImportRecord) -> ImportOutput:
    """Convert persisted import metadata to the API contract."""
    return ImportOutput(
        import_id=import_record.import_id,
        story_id=import_record.story_id,
        source_id=import_record.source_id,
        filename=import_record.filename,
        source_format=import_record.source_format,
        storage_ref=import_record.storage_ref,
        chapter_count=import_record.chapter_count,
        scene_count=import_record.scene_count,
        evidence_anchor_count=import_record.evidence_anchor_count,
        created_at=import_record.created_at,
    )


def _engine_run_output(run: EngineRunRecord) -> EngineRunOutput:
    """Convert persisted engine run metadata to the API contract."""
    return EngineRunOutput(
        run_id=run.run_id,
        project_id=run.project_id,
        story_id=run.story_id,
        import_id=run.import_id,
        status=run.status,
        engine_version=run.engine_version,
        started_at=run.started_at,
        status_updated_at=run.status_updated_at,
        finished_at=run.finished_at,
        error_summary=run.error_summary,
        job_ref=run.job_ref,
    )


def _project_status_output(
    *,
    project_id: str,
    story_count: int,
    imports: Sequence[ImportRecord],
    runs: Sequence[EngineRunRecord],
    snapshots: Sequence[SnapshotRecord],
    exports: Sequence[ExportRecord],
    background_job_queue: BackgroundJobQueue | None,
) -> ProjectStatusResponse:
    """Build metadata-only project status without executing workflows."""
    latest_import = _latest_import(imports)
    latest_run = _latest_run(runs)
    latest_snapshot = _latest_snapshot(snapshots)
    latest_export = _latest_export(exports)
    latest_failure_summary = _latest_failure_summary(runs)
    return ProjectStatusResponse(
        project_id=project_id,
        status=_project_workflow_state(runs=runs, imports=imports, snapshots=snapshots),
        story_count=story_count,
        import_count=len(imports),
        run_count=len(runs),
        latest_import=_project_status_import(latest_import) if latest_import else None,
        latest_engine_run=_project_status_run(latest_run) if latest_run else None,
        worker=_project_status_worker(background_job_queue),
        snapshots=ProjectStatusSnapshots(
            available=bool(snapshots),
            count=len(snapshots),
            latest_snapshot_id=latest_snapshot.snapshot_id if latest_snapshot else None,
            latest_snapshot_kind=latest_snapshot.snapshot_kind if latest_snapshot else None,
        ),
        exports=ProjectStatusExports(
            available=bool(exports),
            count=len(exports),
            latest_export_id=latest_export.export_id if latest_export else None,
            latest_export_kind=latest_export.export_kind if latest_export else None,
            latest_export_format=latest_export.export_format if latest_export else None,
        ),
        latest_failure_summary=latest_failure_summary,
        recent_workflow_events=_recent_workflow_events(
            imports=imports,
            runs=runs,
            snapshots=snapshots,
            exports=exports,
        ),
    )


def _project_outputs_response(
    *,
    project_id: str,
    imports: Sequence[ImportRecord],
    runs: Sequence[EngineRunRecord],
    snapshots: Sequence[SnapshotRecord],
) -> ProjectOutputsResponse:
    """Build project output summaries from persisted snapshots without executing workflows."""
    latest_import = _latest_import(imports)
    latest_run = _latest_run(runs)
    latest_canon = _latest_canon_snapshot(snapshots)
    canon_summary = _project_output_canon_summary(latest_canon)
    canon_payload = _canon_snapshot_metadata(latest_canon) if latest_canon else {}
    return ProjectOutputsResponse(
        project_id=project_id,
        status=_project_workflow_state(runs=runs, imports=imports, snapshots=snapshots),
        latest_import=_project_status_import(latest_import) if latest_import else None,
        latest_engine_run=_project_status_run(latest_run) if latest_run else None,
        canon=canon_summary,
        surfaces=_project_output_surfaces(canon_summary),
        character_profiles=_snapshot_character_profiles(canon_payload),
        world_sheet=_snapshot_world_sheet(canon_payload),
    )


def _project_output_canon_summary(
    snapshot: SnapshotRecord | None,
) -> ProjectOutputCanonSummary:
    """Return a safe canon summary from a persisted snapshot."""
    if snapshot is None:
        return ProjectOutputCanonSummary(available=False)
    payload = _canon_snapshot_metadata(snapshot)
    return ProjectOutputCanonSummary(
        available=True,
        title=_string_payload_value(payload, "title"),
        snapshot_kind=snapshot.snapshot_kind,
        created_at=snapshot.created_at,
        source_id=_string_payload_value(payload, "source_id"),
        chapters=_int_payload_value(payload, "chapters"),
        scenes=_int_payload_value(payload, "scenes"),
        evidence_anchor_count=_int_payload_value(payload, "evidence_anchor_count"),
        extraction_result_count=_int_payload_value(payload, "extraction_result_count"),
        accepted_entity_count=_int_payload_value(payload, "accepted_entity_count"),
        accepted_fact_count=_int_payload_value(payload, "accepted_fact_count"),
        accepted_relationship_count=_int_payload_value(payload, "accepted_relationship_count"),
        accepted_state_change_count=_int_payload_value(payload, "accepted_state_change_count"),
        rejected_candidate_count=_int_payload_value(payload, "rejected_candidate_count"),
        chapter_scene_counts=_chapter_scene_counts(payload),
    )


def _project_output_surfaces(
    canon: ProjectOutputCanonSummary,
) -> tuple[ProjectOutputSurface, ...]:
    """Return alpha output surface availability from canon metadata."""
    if not canon.available:
        return tuple(
            ProjectOutputSurface(
                surface=surface,
                title=title,
                status="waiting",
                summary="Run processing to create a canon snapshot for this project.",
            )
            for surface, title in _output_surface_titles()
        )
    character_status = "ready" if canon.accepted_entity_count > 0 else "waiting"
    world_status = "ready" if canon.accepted_relationship_count > 0 else "waiting"
    timeline_status = "ready" if canon.accepted_state_change_count > 0 else "waiting"
    continuity_status = "ready" if canon.accepted_fact_count > 0 else "waiting"
    return (
        ProjectOutputSurface(
            surface="characters",
            title="Character Cards",
            status=character_status,
            item_count=canon.accepted_entity_count,
            summary=(
                "Character output is backed by accepted canon entity metadata."
                if character_status == "ready"
                else "No accepted character entities have been extracted yet."
            ),
        ),
        ProjectOutputSurface(
            surface="world",
            title="World",
            status=world_status,
            item_count=canon.accepted_relationship_count,
            summary=(
                "World output is backed by accepted canon relationship metadata."
                if world_status == "ready"
                else "No accepted world relationships have been extracted yet."
            ),
        ),
        ProjectOutputSurface(
            surface="timeline",
            title="Timeline",
            status=timeline_status,
            item_count=canon.accepted_state_change_count,
            summary=(
                "Timeline output is backed by accepted state-change metadata."
                if timeline_status == "ready"
                else "No accepted timeline state changes have been extracted yet."
            ),
        ),
        ProjectOutputSurface(
            surface="scenes",
            title="Scene Sheets",
            status="ready",
            item_count=canon.scenes,
            summary="Scene output is backed by imported scene structure and evidence anchors.",
        ),
        ProjectOutputSurface(
            surface="continuity",
            title="Continuity",
            status=continuity_status,
            item_count=canon.accepted_fact_count,
            summary=(
                "Continuity output is backed by accepted canon fact metadata."
                if continuity_status == "ready"
                else "No accepted continuity facts have been extracted yet."
            ),
        ),
        ProjectOutputSurface(
            surface="prompts",
            title="Prompt Packs",
            status="ready",
            item_count=canon.extraction_result_count,
            summary="Prompt-pack output is available from the latest processed scene set.",
        ),
        ProjectOutputSurface(
            surface="exports",
            title="Exports",
            status="ready",
            item_count=canon.scenes,
            summary="Export output can be prepared from the latest canon snapshot.",
        ),
    )


def _output_surface_titles() -> tuple[tuple[str, str], ...]:
    """Return stable workspace output surface names."""
    return (
        ("characters", "Character Cards"),
        ("world", "World"),
        ("timeline", "Timeline"),
        ("scenes", "Scene Sheets"),
        ("continuity", "Continuity"),
        ("prompts", "Prompt Packs"),
        ("exports", "Exports"),
    )


def _latest_canon_snapshot(snapshots: Sequence[SnapshotRecord]) -> SnapshotRecord | None:
    """Return the latest canon snapshot by timestamp and ID."""
    canon_snapshots = tuple(snapshot for snapshot in snapshots if snapshot.snapshot_kind == "canon")
    return _latest_snapshot(canon_snapshots)


def _canon_snapshot_metadata(snapshot: SnapshotRecord) -> Mapping[str, object]:
    """Parse worker canon snapshot metadata without exposing raw payloads to the frontend."""
    if snapshot.content_type != "application/json":
        return {}
    try:
        payload = json.loads(snapshot.serialized_output)
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    return cast(Mapping[str, object], payload)


def _snapshot_character_profiles(
    payload: Mapping[str, object],
) -> tuple[CharacterProfileOutput, ...]:
    """Return persisted character profile panels from snapshot metadata."""
    presentation = _mapping_payload_value(payload, "presentation")
    characters = presentation.get("characters")
    if not isinstance(characters, list):
        return ()
    profiles: list[CharacterProfileOutput] = []
    for character in characters:
        if not isinstance(character, dict):
            continue
        try:
            profiles.append(
                CharacterProfileOutput(
                    character_id=_string_payload_value(character, "character_id"),
                    display_name=_string_payload_value(character, "display_name"),
                    subtitle=_string_payload_value(character, "subtitle"),
                    status=_snapshot_section(character, "status"),
                    current_goal=_snapshot_section(character, "current_goal"),
                    current_equipment=_snapshot_section(character, "current_equipment"),
                    current_abilities=_snapshot_section(character, "current_abilities"),
                    current_assets=_snapshot_section(character, "current_assets"),
                    territory=_snapshot_section(character, "territory"),
                    relationships=_snapshot_section(character, "relationships"),
                    current_limitations=_snapshot_section(
                        character,
                        "current_limitations",
                    ),
                    recent_changes=_snapshot_section(character, "recent_changes"),
                    evidence_summary=_string_payload_value(character, "evidence_summary"),
                )
            )
        except (ValueError, ValidationError):
            continue

    return tuple(profiles)


def _snapshot_world_sheet(payload: Mapping[str, object]) -> WorldSheetOutput | None:
    """Return a persisted world sheet panel from snapshot metadata."""
    presentation = _mapping_payload_value(payload, "presentation")
    world = presentation.get("world")
    if not isinstance(world, dict):
        return None
    entity_sections = world.get("entity_sections")
    if not isinstance(entity_sections, list):
        entity_sections = []
    try:
        return WorldSheetOutput(
            chapter_label=_string_payload_value(world, "chapter_label"),
            entity_sections=tuple(
                _section_from_payload(section)
                for section in entity_sections
                if isinstance(section, dict)
            ),
            evidence_summary=_string_payload_value(world, "evidence_summary"),
        )
    except (ValueError, ValidationError):
        return None


def _snapshot_section(payload: Mapping[str, object], key: str) -> OutputSection:
    """Return one required presentation section from snapshot metadata."""
    return _section_from_payload(_mapping_payload_value(payload, key))


def _section_from_payload(payload: Mapping[str, object]) -> OutputSection:
    """Return one API output section from snapshot metadata."""
    return OutputSection(
        title=_string_payload_value(payload, "title"),
        items=_string_sequence_payload_value(payload, "items"),
    )


def _mapping_payload_value(
    payload: Mapping[str, object],
    key: str,
) -> Mapping[str, object]:
    """Return a nested object payload when present."""
    value = payload.get(key)
    if not isinstance(value, dict):
        return {}
    return cast(Mapping[str, object], value)


def _chapter_scene_counts(
    payload: Mapping[str, object],
) -> tuple[ProjectOutputChapterSummary, ...]:
    """Return per-chapter scene counts from metadata-only snapshot scene IDs."""
    counts: dict[int, int] = {}
    for scene_id in _string_sequence_payload_value(payload, "scene_ids"):
        chapter_index = _chapter_index_from_scene_id(scene_id)
        if chapter_index is None:
            continue
        counts[chapter_index] = counts.get(chapter_index, 0) + 1
    return tuple(
        ProjectOutputChapterSummary(chapter_index=chapter_index, scene_count=scene_count)
        for chapter_index, scene_count in sorted(counts.items())
    )


def _chapter_index_from_scene_id(scene_id: str) -> int | None:
    """Parse a chapter index from normalized imported scene IDs."""
    marker = "_chapter_"
    marker_index = scene_id.find(marker)
    if marker_index < 0:
        return None
    remainder = scene_id[marker_index + len(marker) :]
    value = remainder.split("_", maxsplit=1)[0]
    if not value.isdigit():
        return None
    chapter_index = int(value)
    return chapter_index if chapter_index > 0 else None


def _string_sequence_payload_value(payload: Mapping[str, object], key: str) -> tuple[str, ...]:
    """Return a tuple of string payload values when present."""
    value = payload.get(key)
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, str))


def _string_payload_value(payload: Mapping[str, object], key: str) -> str:
    """Return a string payload value when present."""
    value = payload.get(key)
    return value if isinstance(value, str) else ""


def _int_payload_value(payload: Mapping[str, object], key: str) -> int:
    """Return a non-negative integer payload value when present."""
    value = payload.get(key)
    if isinstance(value, int) and value >= 0:
        return value
    return 0


def _run_status_count(runs: Sequence[EngineRunRecord], status: str) -> int:
    """Return count of runs in one lifecycle status."""
    return sum(1 for run in runs if run.status == status)


def _project_workflow_state(
    *,
    runs: Sequence[EngineRunRecord],
    imports: Sequence[ImportRecord],
    snapshots: Sequence[SnapshotRecord],
) -> str:
    """Return a compact project workflow state for monitoring surfaces."""
    if _run_status_count(runs, "running") > 0:
        return "running"
    if _run_status_count(runs, "pending") > 0:
        return "pending"
    latest_run = _latest_run(runs)
    if latest_run is not None:
        return latest_run.status
    if snapshots:
        return "snapshotted"
    if imports:
        return "imported"
    return "empty"


def _project_status_import(import_record: ImportRecord) -> ProjectStatusImport:
    """Return metadata-only latest import status."""
    return ProjectStatusImport(
        import_id=import_record.import_id,
        story_id=import_record.story_id,
        filename=import_record.filename,
        source_format=import_record.source_format,
        created_at=import_record.created_at,
    )


def _project_status_run(run: EngineRunRecord) -> ProjectStatusRun:
    """Return metadata-only latest engine run status."""
    return ProjectStatusRun(
        run_id=run.run_id,
        story_id=run.story_id,
        import_id=run.import_id,
        status=run.status,
        started_at=run.started_at,
        status_updated_at=run.status_updated_at,
        finished_at=run.finished_at,
        error_summary=run.error_summary,
        job_ref=run.job_ref,
    )


def _project_status_worker(
    background_job_queue: BackgroundJobQueue | None,
) -> ProjectStatusWorker:
    """Return metadata-only worker and job queue state."""
    if background_job_queue is None:
        return ProjectStatusWorker(state="unconfigured")
    snapshot = background_job_queue.snapshot()
    if snapshot.running_jobs > 0:
        state = "running"
    elif snapshot.queued_jobs > 0:
        state = "queued"
    elif snapshot.failed_jobs > 0:
        state = "failed"
    else:
        state = "idle"
    return ProjectStatusWorker(
        state=state,
        total_jobs=snapshot.total_jobs,
        queued_jobs=snapshot.queued_jobs,
        running_jobs=snapshot.running_jobs,
        succeeded_jobs=snapshot.succeeded_jobs,
        failed_jobs=snapshot.failed_jobs,
        next_job_id=snapshot.next_job_id,
    )


def _recent_workflow_events(
    *,
    imports: Sequence[ImportRecord],
    runs: Sequence[EngineRunRecord],
    snapshots: Sequence[SnapshotRecord],
    exports: Sequence[ExportRecord],
) -> tuple[ProjectWorkflowEvent, ...]:
    """Return recent metadata-only workflow events."""
    events = [
        *(_import_event(import_record) for import_record in imports),
        *(_run_event(run) for run in runs),
        *(_snapshot_event(snapshot) for snapshot in snapshots),
        *(_export_event(export) for export in exports),
    ]
    return tuple(
        sorted(
            events,
            key=lambda event: (event.occurred_at, event.event_type, event.summary),
            reverse=True,
        )[:10]
    )


def _import_event(import_record: ImportRecord) -> ProjectWorkflowEvent:
    """Return one metadata-only import workflow event."""
    return ProjectWorkflowEvent(
        event_type="import_saved",
        status="succeeded",
        occurred_at=import_record.created_at,
        story_id=import_record.story_id,
        import_id=import_record.import_id,
        summary=f"Saved {import_record.source_format} import metadata.",
    )


def _run_event(run: EngineRunRecord) -> ProjectWorkflowEvent:
    """Return one metadata-only engine run workflow event."""
    return ProjectWorkflowEvent(
        event_type="engine_run",
        status=run.status,
        occurred_at=run.status_updated_at or run.started_at,
        story_id=run.story_id,
        import_id=run.import_id,
        run_id=run.run_id,
        summary=run.error_summary if run.status == "failed" else f"Run is {run.status}.",
    )


def _snapshot_event(snapshot: SnapshotRecord) -> ProjectWorkflowEvent:
    """Return one metadata-only snapshot workflow event."""
    return ProjectWorkflowEvent(
        event_type="snapshot_created",
        status="succeeded",
        occurred_at=snapshot.created_at,
        story_id=snapshot.story_id,
        run_id=snapshot.run_id,
        snapshot_id=snapshot.snapshot_id,
        summary=f"Created {snapshot.snapshot_kind} snapshot.",
    )


def _export_event(export: ExportRecord) -> ProjectWorkflowEvent:
    """Return one metadata-only export workflow event."""
    return ProjectWorkflowEvent(
        event_type="export_created",
        status="succeeded",
        occurred_at=export.created_at,
        snapshot_id=export.snapshot_id,
        export_id=export.export_id,
        summary=f"Created {export.export_format} {export.export_kind} export.",
    )


def _latest_import(imports: Sequence[ImportRecord]) -> ImportRecord | None:
    """Return latest import by timestamp and ID."""
    if not imports:
        return None
    return max(imports, key=lambda item: (item.created_at, item.import_id))


def _latest_run(runs: Sequence[EngineRunRecord]) -> EngineRunRecord | None:
    """Return latest run by lifecycle timestamp and ID."""
    if not runs:
        return None
    return max(
        runs,
        key=lambda run: (run.status_updated_at or run.started_at, run.run_id),
    )


def _latest_snapshot(snapshots: Sequence[SnapshotRecord]) -> SnapshotRecord | None:
    """Return latest snapshot by timestamp and ID."""
    if not snapshots:
        return None
    return max(snapshots, key=lambda item: (item.created_at, item.snapshot_id))


def _latest_export(exports: Sequence[ExportRecord]) -> ExportRecord | None:
    """Return latest export by timestamp and ID."""
    if not exports:
        return None
    return max(exports, key=lambda item: (item.created_at, item.export_id))


def _latest_failure_summary(runs: Sequence[EngineRunRecord]) -> str:
    """Return the latest run failure summary without source content."""
    failed_run = _latest_run(tuple(run for run in runs if run.status == "failed"))
    if failed_run is None:
        return ""
    return failed_run.error_summary


def _snapshot_output(snapshot: SnapshotRecord) -> SnapshotOutput:
    """Convert persisted snapshot metadata to the API contract."""
    return SnapshotOutput(
        snapshot_id=snapshot.snapshot_id,
        project_id=snapshot.project_id,
        story_id=snapshot.story_id,
        run_id=snapshot.run_id,
        snapshot_kind=snapshot.snapshot_kind,
        content_type=snapshot.content_type,
        serialized_output=snapshot.serialized_output,
        created_at=snapshot.created_at,
    )


def _snapshot_kind_filter(value: str | None) -> SnapshotKind | None:
    """Validate snapshot kind filters and worker payloads."""
    if value is None:
        return None
    allowed = {
        "canon",
        "timeline",
        "character_profile",
        "world_state",
        "scene_sheet",
        "prompt_pack",
        "continuity_report",
    }
    if value not in allowed:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_snapshot_kind",
                "detail": "Snapshot kind is invalid.",
            },
        )
    return cast(SnapshotKind, value)


def _required_snapshot_kind(value: str) -> SnapshotKind:
    """Validate a required snapshot kind value."""
    snapshot_kind = _snapshot_kind_filter(value)
    if snapshot_kind is None:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_snapshot_kind",
                "detail": "Snapshot kind is invalid.",
            },
        )
    return snapshot_kind


def _worker_process_response(summary: BackgroundWorkerRunSummary) -> WorkerProcessResponse:
    """Convert a worker drain summary to the API contract."""
    return WorkerProcessResponse(
        claimed_jobs=summary.claimed_jobs,
        succeeded_jobs=summary.succeeded_jobs,
        failed_jobs=summary.failed_jobs,
    )


def _import_record(
    request: ImportCreateRequest,
    story_id: str,
    source_format: str,
    imported_source: ImportedSource,
) -> ImportRecord:
    """Build persistent import metadata from an inspected source."""
    scene_count = sum(len(chapter.scenes) for chapter in imported_source.story.chapters)
    return ImportRecord(
        import_id=request.import_id,
        story_id=story_id,
        source_id=imported_source.source_id,
        filename=_import_metadata_filename(request.filename),
        source_format=source_format,
        storage_ref=f"api_import://{story_id}/{request.import_id}",
        chapter_count=len(imported_source.story.chapters),
        scene_count=scene_count,
        evidence_anchor_count=len(imported_source.anchors),
        created_at=request.now,
    )


def _require_story_scope(
    repository: ProjectRepository,
    user_id: str,
    project_id: str,
    story_id: str,
) -> StoryRecord:
    """Return a story only when it belongs to the requested project and user."""
    story = repository.get_story(user_id=user_id, story_id=story_id)
    if story.project_id != project_id:
        raise ValueError("Story does not belong to project.")
    return story


def _require_import_scope(
    repository: ProjectRepository,
    user_id: str,
    project_id: str,
    story_id: str,
    import_id: str,
) -> ImportRecord:
    """Return an import only when it belongs to the requested story and project."""
    _require_story_scope(
        repository=repository,
        user_id=user_id,
        project_id=project_id,
        story_id=story_id,
    )
    import_record = repository.get_import(user_id=user_id, import_id=import_id)
    if import_record.story_id != story_id:
        raise ValueError("Import does not belong to story.")
    return import_record


def _reconcile_orphaned_project_runs(
    *,
    repository: ProjectRepository,
    background_job_queue: BackgroundJobQueue | None,
    user_id: str,
    project_id: str,
) -> None:
    """Fail active project runs whose in-memory queue jobs disappeared."""
    if background_job_queue is None:
        return
    now = datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    runs = repository.list_engine_runs_for_project(user_id=user_id, project_id=project_id)
    for run in runs:
        if run.status not in {"pending", "running"}:
            continue
        job_id = _job_id_from_ref(run.job_ref)
        if not job_id or background_job_queue.has_job(job_id):
            continue
        repository.update_engine_run(
            replace(
                run,
                status="failed",
                status_updated_at=now,
                finished_at=now,
                error_summary="Processing stopped before completion. Retry is available.",
            )
        )


def _job_id_from_ref(job_ref: str) -> str:
    """Return the queue job ID from a run job_ref."""
    prefix = "queue://"
    if not job_ref.startswith(prefix):
        return ""
    return job_ref[len(prefix):]


def _active_or_completed_import_run(
    *,
    runs: Sequence[EngineRunRecord],
    import_id: str,
) -> EngineRunRecord | None:
    """Return the latest nonfailed run for an import, if one already exists."""
    matching_runs = tuple(
        run for run in runs if run.import_id == import_id and run.status != "failed"
    )
    return _latest_run(matching_runs)


def _run_is_stale(run: EngineRunRecord, now: str) -> bool:
    """Return true when an active alpha run is old enough to retry."""
    if run.status not in {"pending", "running"}:
        return False
    try:
        run_updated_at = _parse_api_utc(run.status_updated_at or run.started_at)
        submitted_at = _parse_api_utc(now)
    except ValueError:
        return False
    return submitted_at - run_updated_at > ALPHA_ACTIVE_RUN_TIMEOUT


def _parse_api_utc(value: str) -> datetime:
    """Parse API UTC timestamps accepted by alpha routes."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Timestamp cannot be blank.")
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise ValueError("Timestamp must include timezone.")
    return parsed


def _import_run_already_active_detail(run: EngineRunRecord) -> str:
    """Return creator-facing duplicate run guidance."""
    if run.status == "succeeded":
        return "Import processing already completed."
    return "Import processing is already in progress."


def _import_metadata_filename(value: str) -> str:
    """Return basename-only import metadata from a submitted filename."""
    return Path(value.replace("\\", "/")).name


class _MetadataOnlyBackgroundJobHandler:
    """Background handler that acknowledges jobs without creating snapshots."""

    def process(self, _job: BackgroundJob) -> None:
        """Process metadata-only jobs for local Phase 6 run lifecycle testing."""


def _normalized_project_name(value: str) -> str:
    """Return normalized project display text."""
    return " ".join(value.split())


def _normalized_story_title(value: str) -> str:
    """Return normalized story title text."""
    return " ".join(value.split())


def _normalized_machine_token(value: str, label: str) -> str:
    """Return normalized machine-token text or raise a clear validation error."""
    normalized = value.strip().lower()
    if not normalized:
        raise ValueError(f"{label} cannot be blank.")
    if any(character.isspace() for character in normalized):
        raise ValueError(f"{label} cannot contain whitespace.")
    return normalized


def _normalized_locale(value: str) -> str:
    """Return normalized locale text or raise a clear validation error."""
    normalized = value.strip()
    if not normalized:
        raise ValueError("Settings locale cannot be blank.")
    if any(character.isspace() for character in normalized):
        raise ValueError("Settings locale cannot contain whitespace.")
    return normalized


def _project_storage_error(error: PersistenceError) -> HTTPException:
    """Return a stable project storage failure."""
    return HTTPException(
        status_code=503,
        detail={"error": "project_storage_failed", "detail": str(error)},
    )


def _auth_session_response(session: Any) -> AuthSessionResponse:
    """Convert an authenticated session to the API contract."""
    return AuthSessionResponse(
        user_id=session.user.user_id,
        email=session.user.email,
        display_name=session.user.display_name,
        session_token=session.session_token,
        expires_at=session.expires_at,
    )


def _extract_bearer_token(request: Request) -> str:
    """Return a bearer token from the Authorization header."""
    authorization = request.headers.get("Authorization", "").strip()
    scheme, separator, token = authorization.partition(" ")
    if separator and scheme.lower() == "bearer":
        return token.strip()
    return ""


def _platform_limits() -> tuple[str, ...]:
    """Return current Phase 1 platform limits."""
    return (
        "Stateless preview routes only.",
        "No production Project Database configured yet.",
        "Optional API-key protection for workflow routes.",
        "No production background worker queue configured yet.",
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
            path="/v2/auth/register",
            purpose="Register a platform user and issue a session.",
        ),
        ApiRouteCapability(
            method="POST",
            path="/v2/auth/login",
            purpose="Log in a platform user and issue a session.",
        ),
        ApiRouteCapability(
            method="GET",
            path="/v2/auth/me",
            purpose="Return the current authenticated user.",
        ),
        ApiRouteCapability(
            method="POST",
            path="/v2/auth/password-reset/request",
            purpose="Issue a password reset token for delivery.",
        ),
        ApiRouteCapability(
            method="POST",
            path="/v2/auth/password-reset/complete",
            purpose="Complete a password reset with a valid token.",
        ),
        ApiRouteCapability(
            method="GET",
            path="/v2/projects",
            purpose="List durable projects owned by the authenticated user.",
        ),
        ApiRouteCapability(
            method="POST",
            path="/v2/projects",
            purpose="Create a durable project for the authenticated user.",
        ),
        ApiRouteCapability(
            method="GET",
            path="/v2/projects/{project_id}",
            purpose="Return durable project metadata for the authenticated user.",
        ),
        ApiRouteCapability(
            method="GET",
            path="/v2/projects/{project_id}/settings",
            purpose="Return durable project settings for the authenticated user.",
        ),
        ApiRouteCapability(
            method="PUT",
            path="/v2/projects/{project_id}/settings",
            purpose="Update durable project settings for the authenticated user.",
        ),
        ApiRouteCapability(
            method="GET",
            path="/v2/projects/{project_id}/stories",
            purpose="List durable story metadata inside a project.",
        ),
        ApiRouteCapability(
            method="POST",
            path="/v2/projects/{project_id}/stories",
            purpose="Create durable story metadata inside a project.",
        ),
        ApiRouteCapability(
            method="DELETE",
            path="/v2/projects/{project_id}/stories/{story_id}",
            purpose="Hard-delete a story and its scoped import/run/snapshot metadata.",
        ),
        ApiRouteCapability(
            method="GET",
            path="/v2/projects/{project_id}/snapshots",
            purpose="List durable engine output snapshots inside a project.",
        ),
        ApiRouteCapability(
            method="GET",
            path="/v2/projects/{project_id}/outputs",
            purpose="Return processed project output summaries from durable snapshots.",
        ),
        ApiRouteCapability(
            method="GET",
            path="/v2/projects/{project_id}/stories/{story_id}/snapshots",
            purpose="List durable engine output snapshots inside a story.",
        ),
        ApiRouteCapability(
            method="GET",
            path="/v2/projects/{project_id}/stories/{story_id}/imports",
            purpose="List durable import metadata inside a story.",
        ),
        ApiRouteCapability(
            method="POST",
            path="/v2/projects/{project_id}/stories/{story_id}/imports",
            purpose="Inspect and create durable import metadata inside a story.",
        ),
        ApiRouteCapability(
            method="GET",
            path="/v2/projects/{project_id}/runs",
            purpose="List durable engine run metadata inside a project.",
        ),
        ApiRouteCapability(
            method="GET",
            path="/v2/projects/{project_id}/status",
            purpose="Report metadata-only project status for monitoring.",
        ),
        ApiRouteCapability(
            method="POST",
            path="/v2/projects/{project_id}/stories/{story_id}/imports/{import_id}/runs",
            purpose="Submit a saved import for background engine processing.",
        ),
        ApiRouteCapability(
            method="POST",
            path="/v2/workers/process",
            purpose="Drain queued background jobs through the worker boundary.",
        ),
        ApiRouteCapability(
            method="POST",
            path="/v2/workers/runs/{run_id}/snapshots",
            purpose="Persist trusted worker-produced snapshots for completed runs.",
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
            path="/v2/canon/preview",
            purpose="Preview accepted Canon metadata.",
        ),
        ApiRouteCapability(
            method="POST",
            path="/v2/timeline/preview",
            purpose="Preview Timeline order and state-change metadata.",
        ),
        ApiRouteCapability(
            method="POST",
            path="/v2/projects/preview",
            purpose="Preview stateless project metadata after candidate application.",
        ),
        ApiRouteCapability(
            method="POST",
            path="/v2/characters/preview",
            purpose="Preview timeline-aware character profiles.",
        ),
        ApiRouteCapability(
            method="POST",
            path="/v2/scenes/preview",
            purpose="Preview a timeline-aware scene sheet.",
        ),
        ApiRouteCapability(
            method="POST",
            path="/v2/prompts/preview",
            purpose="Preview a canon-backed production prompt pack.",
        ),
        ApiRouteCapability(
            method="POST",
            path="/v2/world/preview",
            purpose="Preview timeline-aware world state.",
        ),
        ApiRouteCapability(
            method="POST",
            path="/v2/continuity/preview",
            purpose="Preview project continuity changes.",
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


def _run_logged_project_result(
    *,
    kind: str,
    request: ExtractionApplyRequest,
    error_code: str,
) -> tuple[ProjectRunResult, str]:
    """Run a stateless workflow and emit metadata-only monitoring logs."""
    started_at = time.perf_counter()
    try:
        result, source_format = _run_project_result(request)
    except ValueError as error:
        _log_workflow_failed(
            kind=kind,
            request=request,
            error_code=error_code,
            error=error,
            duration_ms=_elapsed_ms(started_at),
        )
        raise
    logger.info(
        "api_workflow_succeeded",
        extra={
            **_workflow_request_extra(
                kind=kind,
                request=request,
                status="succeeded",
                source_format=source_format,
            ),
            "duration_ms": _elapsed_ms(started_at),
            "scene_count": _project_result_scene_count(result),
            "extraction_result_count": len(result.extraction_results),
        },
    )
    return result, source_format


def _workflow_request_extra(
    *,
    kind: str,
    request: ImportInspectRequest,
    status: str,
    source_format: str = "",
    error_code: str = "",
) -> dict[str, object]:
    """Return safe workflow metadata for structured API logs."""
    return {
        "workflow_kind": kind,
        "workflow_status": status,
        "error_code": error_code,
        "source_id": request.source_id,
        "source_format": source_format,
        "source_filename": Path(request.filename).name,
        "scene_id": getattr(request, "scene_id", "") or "",
    }


def _log_workflow_failed(
    *,
    kind: str,
    request: ImportInspectRequest,
    error_code: str,
    error: ValueError,
    duration_ms: float | None = None,
) -> None:
    """Emit a metadata-only API workflow failure log."""
    extra = {
        **_workflow_request_extra(
            kind=kind,
            request=request,
            status="failed",
            error_code=error_code,
        ),
        "error_summary": str(error),
    }
    if duration_ms is not None:
        extra["duration_ms"] = duration_ms
    logger.warning(
        "api_workflow_failed",
        extra=extra,
    )


def _elapsed_ms(started_at: float) -> float:
    """Return rounded elapsed milliseconds for metadata-only performance logs."""
    return round((time.perf_counter() - started_at) * 1000, 3)


def _project_result_scene_count(result: ProjectRunResult) -> int:
    """Return imported scene count without touching source prose."""
    return sum(len(chapter.scenes) for chapter in result.imported_source.story.chapters)


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


def _canon_preview_response(
    result: ProjectRunResult,
    source_format: str,
) -> CanonPreviewResponse:
    """Return accepted Canon metadata for a stateless project preview."""
    summary = _extraction_apply_response(result)
    return CanonPreviewResponse(
        source_id=result.imported_source.source_id,
        source_format=source_format,
        accepted_entities=summary.accepted_entities,
        accepted_entity_ids=summary.accepted_entity_ids,
        accepted_facts=summary.accepted_facts,
        accepted_fact_ids=summary.accepted_fact_ids,
        accepted_relationships=summary.accepted_relationships,
        accepted_relationship_ids=summary.accepted_relationship_ids,
        accepted_state_changes=summary.accepted_state_changes,
        accepted_state_change_ids=summary.accepted_state_change_ids,
        rejected_candidate_ids=summary.rejected_candidate_ids,
    )


def _timeline_preview_response(
    result: ProjectRunResult,
    source_format: str,
) -> TimelinePreviewResponse:
    """Return Timeline metadata for a stateless project preview."""
    imported_source = result.imported_source
    return TimelinePreviewResponse(
        source_id=imported_source.source_id,
        source_format=source_format,
        current_scene_id=AevrynProjectRunner.latest_scene_id(result),
        chapter_ids=tuple(chapter.chapter_id for chapter in imported_source.story.chapters),
        scene_map=tuple(
            SceneMapEntry(
                chapter_id=chapter.chapter_id,
                chapter_index=chapter.chapter_index,
                scene_id=scene.scene_id,
                scene_index=scene.scene_index,
                title=scene.title,
            )
            for chapter in imported_source.story.chapters
            for scene in chapter.scenes
        ),
        accepted_state_change_ids=_summary_ids(
            summary.accepted_state_changes for summary in result.update_summaries
        ),
    )


def _project_preview_response(
    result: ProjectRunResult,
    source_format: str,
) -> ProjectPreviewResponse:
    """Return stateless project metadata after import and candidate application."""
    imported_source = result.imported_source
    runner = AevrynProjectRunner()
    return ProjectPreviewResponse(
        source_id=imported_source.source_id,
        source_format=source_format,
        title=imported_source.title,
        chapter_ids=tuple(chapter.chapter_id for chapter in imported_source.story.chapters),
        scene_ids=tuple(
            scene.scene_id
            for chapter in imported_source.story.chapters
            for scene in chapter.scenes
        ),
        current_scene_id=runner.latest_scene_id(result),
        evidence_anchors=len(imported_source.anchors),
        accepted_entity_ids=_summary_ids(
            summary.accepted_entities for summary in result.update_summaries
        ),
        accepted_fact_ids=_summary_ids(
            summary.accepted_facts for summary in result.update_summaries
        ),
        accepted_relationship_ids=_summary_ids(
            summary.accepted_relationships for summary in result.update_summaries
        ),
        accepted_state_change_ids=_summary_ids(
            summary.accepted_state_changes for summary in result.update_summaries
        ),
        available_outputs=(
            ApiLink(rel="characters", href="/v2/characters/preview", method="POST"),
            ApiLink(rel="scene", href="/v2/scenes/preview", method="POST"),
            ApiLink(rel="prompts", href="/v2/prompts/preview", method="POST"),
            ApiLink(rel="world", href="/v2/world/preview", method="POST"),
            ApiLink(rel="continuity", href="/v2/continuity/preview", method="POST"),
            ApiLink(rel="project_outputs", href="/v2/project-outputs/preview", method="POST"),
            ApiLink(rel="exports", href="/v2/exports/preview", method="POST"),
        ),
        platform_limits=_platform_limits(),
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


def _character_preview_response(
    request: ProjectOutputsPreviewRequest,
    result: ProjectRunResult,
    source_format: str,
) -> CharacterPreviewResponse:
    """Return character profiles for a stateless project preview."""
    runner = AevrynProjectRunner()
    scene_id = request.scene_id or runner.latest_scene_id(result)
    character_ids = request.character_ids or _accepted_character_ids(result)
    presenter = PresentationEngine()
    return CharacterPreviewResponse(
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
    )


def _scene_preview_response(
    request: ProjectOutputsPreviewRequest,
    result: ProjectRunResult,
    source_format: str,
) -> ScenePreviewResponse:
    """Return a scene sheet for a stateless project preview."""
    runner = AevrynProjectRunner()
    scene_id = request.scene_id or runner.latest_scene_id(result)
    context = runner.build_scene_context(
        result=result,
        scene_id=scene_id,
        character_ids=request.character_ids or _accepted_character_ids(result),
    )
    pack = CanonPromptBuilder().build_production_pack(context)
    scene_sheet = PresentationEngine().scene_sheet(context=context, analysis=pack.analysis)
    return ScenePreviewResponse(
        source_id=result.imported_source.source_id,
        source_format=source_format,
        scene_id=scene_id,
        scene_sheet=_scene_sheet_output(
            scene_sheet,
            source_quotes=_source_quotes(result),
        ),
    )


def _prompt_preview_response(
    request: ProjectOutputsPreviewRequest,
    result: ProjectRunResult,
    source_format: str,
) -> PromptPreviewResponse:
    """Return a production pack for a stateless project preview."""
    runner = AevrynProjectRunner()
    scene_id = request.scene_id or runner.latest_scene_id(result)
    context = runner.build_scene_context(
        result=result,
        scene_id=scene_id,
        character_ids=request.character_ids or _accepted_character_ids(result),
    )
    pack = CanonPromptBuilder().build_production_pack(context)
    presenter = PresentationEngine()
    scene_sheet = presenter.scene_sheet(context=context, analysis=pack.analysis)
    return PromptPreviewResponse(
        source_id=result.imported_source.source_id,
        source_format=source_format,
        scene_id=scene_id,
        production_pack=_production_pack_output(
            presenter.production_pack(pack=pack, scene=scene_sheet),
            source_quotes=_source_quotes(result),
        ),
    )


def _continuity_preview_response(
    result: ProjectRunResult,
    source_format: str,
) -> ContinuityPreviewResponse:
    """Return a continuity report for a stateless project preview."""
    return ContinuityPreviewResponse(
        source_id=result.imported_source.source_id,
        source_format=source_format,
        continuity_report=_continuity_report_output(
            AevrynProjectRunner().build_continuity_report(result)
        ),
    )


def _world_preview_response(
    request: ProjectOutputsPreviewRequest,
    result: ProjectRunResult,
    source_format: str,
) -> WorldPreviewResponse:
    """Return a world sheet for a stateless project preview."""
    runner = AevrynProjectRunner()
    scene_id = request.scene_id or runner.latest_scene_id(result)
    world_state = runner.build_world_state_at_scene(
        result=result,
        entity_ids=request.world_entity_ids,
        scene_id=scene_id,
    )
    return WorldPreviewResponse(
        source_id=result.imported_source.source_id,
        source_format=source_format,
        scene_id=scene_id,
        world_sheet=_world_sheet_output(PresentationEngine().world_sheet(world_state)),
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
        report = _safe_continuity_report(runner.build_continuity_report(result))
        if export_format == "markdown":
            return export_engine.continuity_report_markdown(report)
        if export_format == "json":
            return export_engine.continuity_report_json(report)

    raise ValueError(f"Unsupported export preview: {kind}/{export_format}")


def _safe_continuity_report(report: ContinuityReport) -> ContinuityReport:
    """Return a continuity report without exact source prose for API previews."""
    return ContinuityReport(
        source_id=report.source_id,
        scenes=tuple(_safe_continuity_scene(scene) for scene in report.scenes),
    )


def _safe_continuity_scene(scene: ContinuitySceneReport) -> ContinuitySceneReport:
    """Return one continuity scene report without evidence quotes."""
    return ContinuitySceneReport(
        scene_id=scene.scene_id,
        new=tuple(_safe_continuity_record(record) for record in scene.new),
        updated=tuple(_safe_continuity_record(record) for record in scene.updated),
        still_known=tuple(_safe_continuity_record(record) for record in scene.still_known),
        invalidated=tuple(
            _safe_continuity_record(record) for record in scene.invalidated
        ),
    )


def _safe_continuity_record(record: ContinuityRecord) -> ContinuityRecord:
    """Return one continuity record with evidence anchors but no quote text."""
    return ContinuityRecord(
        record_id=record.record_id,
        record_type=record.record_type,
        description=record.description,
        evidence_id=record.evidence_id,
        chapter_id=record.chapter_id,
        scene_id=record.scene_id,
    )


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
