"""Pydantic models for the Aevryn Backend API contract."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StorageHealth(BaseModel):
    """Storage adapter availability metadata for health checks."""

    model_config = ConfigDict(frozen=True)

    project_storage: str
    import_content_storage: str


class HealthResponse(BaseModel):
    """Health response for the Backend API."""

    model_config = ConfigDict(frozen=True)

    status: str
    api_version: str
    engine: str
    storage: StorageHealth


class SourceFormat(BaseModel):
    """One source format supported or deferred by Story Import adapters."""

    model_config = ConfigDict(frozen=True)

    extension: str
    status: str
    adapter: str
    evidence_anchor_status: str
    notes: str


class SourceFormatsResponse(BaseModel):
    """Supported and deferred native source format metadata."""

    model_config = ConfigDict(frozen=True)

    supported: tuple[SourceFormat, ...]
    deferred: tuple[SourceFormat, ...]


class ApiRouteCapability(BaseModel):
    """One public API route exposed by the Backend API."""

    model_config = ConfigDict(frozen=True)

    method: str
    path: str
    purpose: str


class ApiLink(BaseModel):
    """Named API link returned by the version index."""

    model_config = ConfigDict(frozen=True)

    rel: str
    href: str
    method: str


class ApiIndexResponse(BaseModel):
    """Versioned Backend API index response."""

    model_config = ConfigDict(frozen=True)

    api_version: str
    engine: str
    phase: str
    links: tuple[ApiLink, ...]
    platform_limits: tuple[str, ...]


class ExportCapability(BaseModel):
    """One export kind and the formats supported by the API."""

    model_config = ConfigDict(frozen=True)

    export_kind: str
    formats: tuple[str, ...]


class CapabilitiesResponse(BaseModel):
    """Discoverable Phase 1 Backend API capability metadata."""

    model_config = ConfigDict(frozen=True)

    api_version: str
    engine: str
    phase: str
    routes: tuple[ApiRouteCapability, ...]
    source_formats: SourceFormatsResponse
    export_capabilities: tuple[ExportCapability, ...]
    platform_limits: tuple[str, ...]


class AuthRegisterRequest(BaseModel):
    """Request to register a platform user."""

    model_config = ConfigDict(frozen=True)

    user_id: str = Field(min_length=1)
    email: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    password: str = Field(min_length=1)
    now: str = Field(min_length=1)


class AuthLoginRequest(BaseModel):
    """Request to log in a platform user."""

    model_config = ConfigDict(frozen=True)

    email: str = Field(min_length=1)
    password: str = Field(min_length=1)
    now: str = Field(min_length=1)


class AuthPasswordResetRequest(BaseModel):
    """Request to issue a password reset token."""

    model_config = ConfigDict(frozen=True)

    email: str = Field(min_length=1)
    reset_id: str = Field(min_length=1)
    now: str = Field(min_length=1)


class AuthPasswordResetCompleteRequest(BaseModel):
    """Request to complete a password reset."""

    model_config = ConfigDict(frozen=True)

    reset_token: str = Field(min_length=1)
    new_password: str = Field(min_length=1)
    now: str = Field(min_length=1)


class AuthSessionResponse(BaseModel):
    """Authenticated user session response."""

    model_config = ConfigDict(frozen=True)

    user_id: str
    email: str
    display_name: str
    session_token: str
    expires_at: str


class AuthPasswordResetResponse(BaseModel):
    """Password reset token response for delivery by the platform."""

    model_config = ConfigDict(frozen=True)

    user_id: str
    reset_token: str
    expires_at: str


class AuthMeResponse(BaseModel):
    """Current authenticated user response."""

    model_config = ConfigDict(frozen=True)

    user_id: str
    email: str
    display_name: str


class AuthMessageResponse(BaseModel):
    """Simple authentication action response."""

    model_config = ConfigDict(frozen=True)

    status: str


class ProjectCreateRequest(BaseModel):
    """Request to create a durable platform project."""

    model_config = ConfigDict(frozen=True)

    project_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    now: str = Field(min_length=1)


class ProjectOutput(BaseModel):
    """Ownership-safe project metadata returned by the API."""

    model_config = ConfigDict(frozen=True)

    project_id: str
    name: str
    created_at: str
    updated_at: str


class ProjectListResponse(BaseModel):
    """Projects owned by the authenticated user."""

    model_config = ConfigDict(frozen=True)

    projects: tuple[ProjectOutput, ...]


class ProjectSettingsRequest(BaseModel):
    """Request to update durable project settings."""

    model_config = ConfigDict(frozen=True)

    default_export_format: str = Field(min_length=1)
    locale: str = Field(min_length=1)


class ProjectSettingsResponse(BaseModel):
    """Durable project settings returned by the API."""

    model_config = ConfigDict(frozen=True)

    project_id: str
    default_export_format: str
    locale: str


class StoryCreateRequest(BaseModel):
    """Request to create durable story metadata inside a project."""

    model_config = ConfigDict(frozen=True)

    story_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    now: str = Field(min_length=1)


class StoryOutput(BaseModel):
    """Ownership-safe story metadata returned by the API."""

    model_config = ConfigDict(frozen=True)

    story_id: str
    project_id: str
    title: str
    created_at: str
    updated_at: str


class StoryListResponse(BaseModel):
    """Stories inside an authenticated project."""

    model_config = ConfigDict(frozen=True)

    stories: tuple[StoryOutput, ...]


class ImportOutput(BaseModel):
    """Ownership-safe source import metadata returned by the API."""

    model_config = ConfigDict(frozen=True)

    import_id: str
    story_id: str
    source_id: str
    filename: str
    source_format: str
    storage_ref: str
    chapter_count: int
    scene_count: int
    evidence_anchor_count: int
    created_at: str


class ImportListResponse(BaseModel):
    """Saved source import metadata inside an authenticated story."""

    model_config = ConfigDict(frozen=True)

    imports: tuple[ImportOutput, ...]


class EngineRunCreateRequest(BaseModel):
    """Request to submit a saved import for background engine processing."""

    model_config = ConfigDict(frozen=True)

    run_id: str = Field(min_length=1)
    job_id: str = Field(min_length=1)
    now: str = Field(min_length=1)


class EngineRunOutput(BaseModel):
    """Ownership-safe engine run metadata returned by the API."""

    model_config = ConfigDict(frozen=True)

    run_id: str
    project_id: str
    story_id: str
    import_id: str
    status: str
    engine_version: str
    started_at: str
    status_updated_at: str | None = None
    finished_at: str | None = None
    error_summary: str = ""
    job_ref: str = ""


class EngineRunListResponse(BaseModel):
    """Engine runs inside an authenticated project."""

    model_config = ConfigDict(frozen=True)

    runs: tuple[EngineRunOutput, ...]


class ProjectStatusImport(BaseModel):
    """Metadata-only latest import summary for project monitoring."""

    model_config = ConfigDict(frozen=True)

    import_id: str
    story_id: str
    filename: str
    source_format: str
    created_at: str


class ProjectStatusRun(BaseModel):
    """Metadata-only latest engine run summary for project monitoring."""

    model_config = ConfigDict(frozen=True)

    run_id: str
    story_id: str
    import_id: str
    status: str
    started_at: str
    status_updated_at: str | None = None
    finished_at: str | None = None
    error_summary: str = ""
    job_ref: str = ""


class ProjectStatusWorker(BaseModel):
    """Queue and worker state visible to project monitoring."""

    model_config = ConfigDict(frozen=True)

    state: str
    total_jobs: int = 0
    queued_jobs: int = 0
    running_jobs: int = 0
    succeeded_jobs: int = 0
    failed_jobs: int = 0
    next_job_id: str = ""


class ProjectStatusSnapshots(BaseModel):
    """Snapshot availability visible to project monitoring."""

    model_config = ConfigDict(frozen=True)

    available: bool
    count: int
    latest_snapshot_id: str | None = None
    latest_snapshot_kind: str | None = None


class ProjectStatusExports(BaseModel):
    """Export availability visible to project monitoring."""

    model_config = ConfigDict(frozen=True)

    available: bool
    count: int
    latest_export_id: str | None = None
    latest_export_kind: str | None = None
    latest_export_format: str | None = None


class ProjectWorkflowEvent(BaseModel):
    """Recent metadata-only workflow event for monitoring surfaces."""

    model_config = ConfigDict(frozen=True)

    event_type: str
    status: str
    occurred_at: str
    story_id: str = ""
    import_id: str = ""
    run_id: str = ""
    snapshot_id: str = ""
    export_id: str = ""
    summary: str = ""


class ProjectStatusResponse(BaseModel):
    """Metadata-only project status for monitoring surfaces."""

    model_config = ConfigDict(frozen=True)

    project_id: str
    status: str
    story_count: int
    import_count: int
    run_count: int
    latest_import: ProjectStatusImport | None = None
    latest_engine_run: ProjectStatusRun | None = None
    worker: ProjectStatusWorker
    snapshots: ProjectStatusSnapshots
    exports: ProjectStatusExports
    latest_failure_summary: str = ""
    recent_workflow_events: tuple[ProjectWorkflowEvent, ...]


class ProjectOutputCanonSummary(BaseModel):
    """Metadata-only summary of the latest persisted canon snapshot."""

    model_config = ConfigDict(frozen=True)

    available: bool
    title: str = ""
    snapshot_kind: str = ""
    created_at: str = ""
    source_id: str = ""
    chapters: int = 0
    scenes: int = 0
    evidence_anchor_count: int = 0
    extraction_result_count: int = 0
    accepted_entity_count: int = 0
    accepted_fact_count: int = 0
    accepted_relationship_count: int = 0
    accepted_state_change_count: int = 0
    rejected_candidate_count: int = 0
    chapter_scene_counts: tuple[ProjectOutputChapterSummary, ...] = ()


class ProjectOutputChapterSummary(BaseModel):
    """Metadata-only scene count for one imported chapter."""

    model_config = ConfigDict(frozen=True)

    chapter_index: int
    scene_count: int


class ProjectOutputSurface(BaseModel):
    """Creator-facing availability summary for one project output surface."""

    model_config = ConfigDict(frozen=True)

    surface: str
    title: str
    status: str
    summary: str
    item_count: int = 0


class ProjectIdentityReviewItem(BaseModel):
    """Metadata-only unresolved or ambiguous identity reference."""

    model_config = ConfigDict(frozen=True)

    status: str
    chapter_id: str = ""
    scene_id: str = ""
    evidence_anchor_id: str
    reference_kind: str = "unknown"
    reference_label: str = "Reference needs review"
    candidate_count: int = 0
    confidence: float = 0.0
    reason: str = ""


class ProjectTranslationReviewItem(BaseModel):
    """Metadata-only translation issue that needs review."""

    model_config = ConfigDict(frozen=True)

    issue_code: str
    issue_label: str
    chapter_id: str = ""
    scene_id: str = ""
    evidence_anchor_count: int = 0
    reason: str = ""


class ProjectLanguageIdentitySummary(BaseModel):
    """Metadata-only Phase 12 language and identity summary."""

    model_config = ConfigDict(frozen=True)

    translation_unit_count: int = 0
    translation_review_count: int = 0
    translation_review_items: tuple[ProjectTranslationReviewItem, ...] = ()
    identity_decision_count: int = 0
    identity_resolved_count: int = 0
    identity_ambiguous_count: int = 0
    identity_unresolved_count: int = 0
    identity_review_items: tuple[ProjectIdentityReviewItem, ...] = ()


class ProjectTimelineChangeOutput(BaseModel):
    """One creator-facing state change in story order."""

    model_config = ConfigDict(frozen=True)

    change_id: str
    chapter_index: int
    scene_index: int
    chapter_title: str
    scene_title: str
    entity_id: str
    entity_name: str
    attribute: str
    value: str


class ProjectOutputsResponse(BaseModel):
    """API-owned project output summary for alpha workspace surfaces."""

    model_config = ConfigDict(frozen=True)

    project_id: str
    status: str
    latest_import: ProjectStatusImport | None = None
    latest_engine_run: ProjectStatusRun | None = None
    canon: ProjectOutputCanonSummary
    surfaces: tuple[ProjectOutputSurface, ...]
    language_identity: ProjectLanguageIdentitySummary = ProjectLanguageIdentitySummary()
    character_profiles: tuple[CharacterProfileOutput, ...] = ()
    world_sheet: WorldSheetOutput | None = None
    timeline_changes: tuple[ProjectTimelineChangeOutput, ...] = ()
    scene_sheets: tuple[SceneSheetOutput, ...] = ()
    prompt_packs: tuple[ProductionPackOutput, ...] = ()
    continuity_report: ContinuityReportOutput | None = None
    export_options: tuple[ProjectExportOptionOutput, ...] = ()


class SnapshotStoreRequest(BaseModel):
    """Trusted worker request to persist one engine output snapshot."""

    model_config = ConfigDict(frozen=True)

    snapshot_id: str = Field(min_length=1)
    snapshot_kind: str = Field(min_length=1)
    content_type: str = Field(min_length=1)
    serialized_output: str = Field(min_length=1)
    now: str = Field(min_length=1)


class SnapshotOutput(BaseModel):
    """Ownership-safe immutable engine output snapshot metadata."""

    model_config = ConfigDict(frozen=True)

    snapshot_id: str
    project_id: str
    story_id: str
    run_id: str
    snapshot_kind: str
    content_type: str
    serialized_output: str
    created_at: str


class SnapshotListResponse(BaseModel):
    """Snapshots visible inside an authenticated project or story."""

    model_config = ConfigDict(frozen=True)

    snapshots: tuple[SnapshotOutput, ...]


class ExportCreateRequest(BaseModel):
    """Request to persist a generated export from a durable snapshot."""

    model_config = ConfigDict(frozen=True)

    export_id: str = Field(min_length=1)
    snapshot_id: str = Field(min_length=1)
    export_format: str = Field(default="json", min_length=1)
    filename: str | None = None
    now: str = Field(min_length=1)


class ExportOutput(BaseModel):
    """Ownership-safe generated export metadata."""

    model_config = ConfigDict(frozen=True)

    export_id: str
    project_id: str
    snapshot_id: str
    export_kind: str
    export_format: str
    filename: str
    content_type: str
    size: int
    checksum: str
    created_at: str


class ExportListResponse(BaseModel):
    """Generated exports visible inside an authenticated project."""

    model_config = ConfigDict(frozen=True)

    exports: tuple[ExportOutput, ...]


class WorkerProcessRequest(BaseModel):
    """Request to drain queued background jobs through the worker boundary."""

    model_config = ConfigDict(frozen=True)

    started_at: str = Field(min_length=1)
    finished_at: str = Field(min_length=1)
    max_jobs: int = Field(ge=1)


class WorkerProcessResponse(BaseModel):
    """Summary returned after processing available background jobs."""

    model_config = ConfigDict(frozen=True)

    claimed_jobs: int
    succeeded_jobs: int
    failed_jobs: int


class ImportInspectRequest(BaseModel):
    """Request to inspect imported source structure without storing a project."""

    model_config = ConfigDict(frozen=True)

    source_id: str = Field(min_length=1)
    filename: str = Field(min_length=1)
    content_base64: str = Field(min_length=1)
    title: str | None = None


class ImportCreateRequest(ImportInspectRequest):
    """Request to inspect and persist source import metadata inside a story."""

    import_id: str = Field(min_length=1)
    now: str = Field(min_length=1)


class ExtractionPromptRequest(ImportInspectRequest):
    """Request to build an evidence-bounded extraction prompt."""

    scene_id: str | None = None


class ExtractionApplyRequest(ImportInspectRequest):
    """Request to apply evidence-bounded extraction candidates."""

    ai_response: dict[str, Any]
    scene_id: str | None = None


class ProjectPreviewRequest(ExtractionApplyRequest):
    """Request to preview stateless project metadata after candidate application."""


class CanonPreviewRequest(ExtractionApplyRequest):
    """Request to preview accepted Canon metadata from a stateless project run."""


class TimelinePreviewRequest(ExtractionApplyRequest):
    """Request to preview Timeline metadata from a stateless project run."""


class ProjectOutputsPreviewRequest(ExtractionApplyRequest):
    """Request to preview platform outputs from a stateless project run."""

    character_ids: tuple[str, ...] = ()
    world_entity_ids: tuple[str, ...] = ()


class CharacterPreviewRequest(ProjectOutputsPreviewRequest):
    """Request to preview character profiles from a stateless project run."""


class ScenePreviewRequest(ProjectOutputsPreviewRequest):
    """Request to preview a scene sheet from a stateless project run."""


class PromptPreviewRequest(ProjectOutputsPreviewRequest):
    """Request to preview a production pack from a stateless project run."""


class WorldPreviewRequest(ProjectOutputsPreviewRequest):
    """Request to preview world state from a stateless project run."""


class ContinuityPreviewRequest(ProjectOutputsPreviewRequest):
    """Request to preview a continuity report from a stateless project run."""


class ExportPreviewRequest(ProjectOutputsPreviewRequest):
    """Request to preview one serialized export from a stateless project run."""

    export_kind: str = Field(min_length=1)
    export_format: str = Field(default="markdown", min_length=1)
    character_id: str | None = None


class SceneMapEntry(BaseModel):
    """Imported scene location exposed by the API."""

    model_config = ConfigDict(frozen=True)

    chapter_id: str
    chapter_index: int
    scene_id: str
    scene_index: int
    title: str


class EvidenceAnchorPreview(BaseModel):
    """Bounded evidence-anchor metadata without source quote text."""

    model_config = ConfigDict(frozen=True)

    anchor_id: str
    chapter_id: str
    scene_id: str
    paragraph_index: int
    sentence_index: int


class ImportInspectResponse(BaseModel):
    """Imported source structure returned by the Import API."""

    model_config = ConfigDict(frozen=True)

    source_id: str
    source_format: str
    title: str
    chapters: int
    chapter_ids: tuple[str, ...]
    scenes: int
    scene_ids: tuple[str, ...]
    scene_map: tuple[SceneMapEntry, ...]
    paragraphs: int
    evidence_anchors: int
    first_evidence_anchors: tuple[EvidenceAnchorPreview, ...]


class ExtractionPromptResponse(BaseModel):
    """Evidence-bounded extraction prompt response."""

    model_config = ConfigDict(frozen=True)

    source_id: str
    source_format: str
    scene_id: str
    evidence_anchor_count: int
    prompt: str


class ExtractionSceneResult(BaseModel):
    """Candidate counts for one extracted scene."""

    model_config = ConfigDict(frozen=True)

    scene_id: str
    entities: int
    facts: int
    relationships: int
    state_changes: int


class ExtractionApplyResponse(BaseModel):
    """Canon Updating summary for an applied extraction payload."""

    model_config = ConfigDict(frozen=True)

    results: tuple[ExtractionSceneResult, ...]
    accepted_entities: int
    accepted_entity_ids: tuple[str, ...]
    accepted_facts: int
    accepted_fact_ids: tuple[str, ...]
    accepted_relationships: int
    accepted_relationship_ids: tuple[str, ...]
    accepted_state_changes: int
    accepted_state_change_ids: tuple[str, ...]
    rejected_candidate_ids: tuple[str, ...]


class CanonPreviewResponse(BaseModel):
    """Canon API preview response."""

    model_config = ConfigDict(frozen=True)

    source_id: str
    source_format: str
    accepted_entities: int
    accepted_entity_ids: tuple[str, ...]
    accepted_facts: int
    accepted_fact_ids: tuple[str, ...]
    accepted_relationships: int
    accepted_relationship_ids: tuple[str, ...]
    accepted_state_changes: int
    accepted_state_change_ids: tuple[str, ...]
    rejected_candidate_ids: tuple[str, ...]


class TimelinePreviewResponse(BaseModel):
    """Timeline API preview response."""

    model_config = ConfigDict(frozen=True)

    source_id: str
    source_format: str
    current_scene_id: str
    chapter_ids: tuple[str, ...]
    scene_map: tuple[SceneMapEntry, ...]
    accepted_state_change_ids: tuple[str, ...]


class ProjectPreviewResponse(BaseModel):
    """Stateless project metadata returned by the Project Management API."""

    model_config = ConfigDict(frozen=True)

    source_id: str
    source_format: str
    title: str
    chapter_ids: tuple[str, ...]
    scene_ids: tuple[str, ...]
    current_scene_id: str
    evidence_anchors: int
    accepted_entity_ids: tuple[str, ...]
    accepted_fact_ids: tuple[str, ...]
    accepted_relationship_ids: tuple[str, ...]
    accepted_state_change_ids: tuple[str, ...]
    available_outputs: tuple[ApiLink, ...]
    platform_limits: tuple[str, ...]


class OutputSection(BaseModel):
    """Human-readable named section returned by the platform API."""

    model_config = ConfigDict(frozen=True)

    title: str
    items: tuple[str, ...]


class ProjectExportOptionOutput(BaseModel):
    """One alpha-safe export option available from processed output."""

    model_config = ConfigDict(frozen=True)

    export_kind: str
    formats: tuple[str, ...]
    label: str


class CharacterProfileOutput(BaseModel):
    """Human-readable character profile output."""

    model_config = ConfigDict(frozen=True)

    character_id: str
    display_name: str
    subtitle: str
    race: OutputSection
    gender: OutputSection
    status: OutputSection
    current_goal: OutputSection
    current_equipment: OutputSection
    current_abilities: OutputSection
    current_assets: OutputSection
    territory: OutputSection
    relationships: OutputSection
    current_limitations: OutputSection
    recent_changes: OutputSection
    evidence_summary: str


class SceneSheetOutput(BaseModel):
    """Human-readable scene sheet output."""

    model_config = ConfigDict(frozen=True)

    scene_id: str
    title: str
    chapter_label: str
    location: OutputSection
    characters_present: OutputSection
    mood: OutputSection
    purpose: OutputSection
    visual_highlights: OutputSection
    continuity_changes: OutputSection
    environment: OutputSection
    evidence_summary: str


class ProductionPackOutput(BaseModel):
    """Human-readable production pack output."""

    model_config = ConfigDict(frozen=True)

    scene: SceneSheetOutput
    image_prompt: OutputSection
    narration_prompt: OutputSection
    camera_prompt: OutputSection
    animation_prompt: OutputSection


class WorldSheetOutput(BaseModel):
    """Human-readable world sheet output."""

    model_config = ConfigDict(frozen=True)

    chapter_label: str
    entity_sections: tuple[OutputSection, ...]
    evidence_summary: str


class ContinuityRecordOutput(BaseModel):
    """One continuity record exposed by the platform API."""

    model_config = ConfigDict(frozen=True)

    record_id: str
    record_type: str
    description: str
    evidence_id: str
    chapter_id: str
    scene_id: str


class ContinuitySceneOutput(BaseModel):
    """Continuity changes for one scene."""

    model_config = ConfigDict(frozen=True)

    scene_id: str
    new: tuple[ContinuityRecordOutput, ...]
    updated: tuple[ContinuityRecordOutput, ...]
    still_known: tuple[ContinuityRecordOutput, ...]
    invalidated: tuple[ContinuityRecordOutput, ...]


class ContinuityReportOutput(BaseModel):
    """Project-level continuity report output."""

    model_config = ConfigDict(frozen=True)

    source_id: str
    scenes: tuple[ContinuitySceneOutput, ...]


class CharacterPreviewResponse(BaseModel):
    """Character API preview response."""

    model_config = ConfigDict(frozen=True)

    source_id: str
    source_format: str
    scene_id: str
    character_profiles: tuple[CharacterProfileOutput, ...]


class ScenePreviewResponse(BaseModel):
    """Scene API preview response."""

    model_config = ConfigDict(frozen=True)

    source_id: str
    source_format: str
    scene_id: str
    scene_sheet: SceneSheetOutput


class PromptPreviewResponse(BaseModel):
    """Prompt API preview response."""

    model_config = ConfigDict(frozen=True)

    source_id: str
    source_format: str
    scene_id: str
    production_pack: ProductionPackOutput


class WorldPreviewResponse(BaseModel):
    """World API preview response."""

    model_config = ConfigDict(frozen=True)

    source_id: str
    source_format: str
    scene_id: str
    world_sheet: WorldSheetOutput


class ContinuityPreviewResponse(BaseModel):
    """Continuity API preview response."""

    model_config = ConfigDict(frozen=True)

    source_id: str
    source_format: str
    continuity_report: ContinuityReportOutput


class ProjectOutputsPreviewResponse(BaseModel):
    """Stateless platform output preview generated through the engine."""

    model_config = ConfigDict(frozen=True)

    source_id: str
    source_format: str
    scene_id: str
    character_profiles: tuple[CharacterProfileOutput, ...]
    scene_sheet: SceneSheetOutput
    production_pack: ProductionPackOutput
    world_sheet: WorldSheetOutput
    continuity_report: ContinuityReportOutput


class ExportPreviewResponse(BaseModel):
    """Serialized export preview generated through the Export Engine."""

    model_config = ConfigDict(frozen=True)

    source_id: str
    source_format: str
    scene_id: str
    export_kind: str
    export_format: str
    filename: str
    content_type: str
    content: str


class ErrorResponse(BaseModel):
    """Structured API error response."""

    model_config = ConfigDict(frozen=True)

    error: str
    detail: str
