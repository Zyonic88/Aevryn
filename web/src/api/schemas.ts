import { z } from "zod";

export const healthSchema = z.object({
  status: z.string(),
  api_version: z.string(),
  engine: z.string(),
  storage: z.object({
    project_storage: z.string(),
    import_content_storage: z.string(),
  }),
});

export const routeCapabilitySchema = z.object({
  method: z.string(),
  path: z.string(),
  purpose: z.string(),
});

export const sourceFormatSchema = z.object({
  extension: z.string(),
  status: z.string(),
  adapter: z.string(),
  evidence_anchor_status: z.string(),
  notes: z.string(),
});

export const sourceFormatsSchema = z.object({
  supported: z.array(sourceFormatSchema),
  deferred: z.array(sourceFormatSchema),
});

export const exportCapabilitySchema = z.object({
  export_kind: z.string(),
  formats: z.array(z.string()),
});

export const capabilitiesSchema = z.object({
  api_version: z.string(),
  engine: z.string(),
  phase: z.string(),
  routes: z.array(routeCapabilitySchema),
  source_formats: sourceFormatsSchema,
  export_capabilities: z.array(exportCapabilitySchema),
  platform_limits: z.array(z.string()),
});

export const authSessionSchema = z.object({
  user_id: z.string(),
  email: z.string(),
  display_name: z.string(),
  session_token: z.string(),
  refresh_token: z.string().optional(),
  expires_at: z.string(),
});

export const authMeSchema = z.object({
  user_id: z.string(),
  email: z.string(),
  display_name: z.string(),
});

export const projectSchema = z.object({
  project_id: z.string(),
  name: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
});

export const projectListSchema = z.object({
  projects: z.array(projectSchema),
});

export const projectSettingsSchema = z.object({
  project_id: z.string(),
  default_export_format: z.string(),
  locale: z.string(),
});

export const storySchema = z.object({
  story_id: z.string(),
  project_id: z.string(),
  title: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
});

export const storyListSchema = z.object({
  stories: z.array(storySchema),
});

export const importRecordSchema = z.object({
  import_id: z.string(),
  story_id: z.string(),
  source_id: z.string(),
  filename: z.string(),
  source_format: z.string(),
  storage_ref: z.string(),
  chapter_count: z.number(),
  scene_count: z.number(),
  evidence_anchor_count: z.number(),
  created_at: z.string(),
});

export const importListSchema = z.object({
  imports: z.array(importRecordSchema),
});

export const engineRunSchema = z.object({
  run_id: z.string(),
  project_id: z.string(),
  story_id: z.string(),
  import_id: z.string(),
  status: z.string(),
  engine_version: z.string(),
  started_at: z.string(),
  status_updated_at: z.string().nullable(),
  finished_at: z.string().nullable(),
  error_summary: z.string(),
  job_ref: z.string(),
});

export const engineRunListSchema = z.object({
  runs: z.array(engineRunSchema),
});

export const workerProcessSchema = z.object({
  claimed_jobs: z.number(),
  succeeded_jobs: z.number(),
  failed_jobs: z.number(),
});

export const projectStatusImportSchema = z.object({
  import_id: z.string(),
  story_id: z.string(),
  filename: z.string(),
  source_format: z.string(),
  created_at: z.string(),
});

export const projectStatusRunSchema = z.object({
  run_id: z.string(),
  story_id: z.string(),
  import_id: z.string(),
  status: z.string(),
  started_at: z.string(),
  status_updated_at: z.string().nullable(),
  finished_at: z.string().nullable(),
  error_summary: z.string(),
  job_ref: z.string(),
});

export const projectStatusWorkerSchema = z.object({
  state: z.string(),
  total_jobs: z.number(),
  queued_jobs: z.number(),
  running_jobs: z.number(),
  succeeded_jobs: z.number(),
  failed_jobs: z.number(),
  next_job_id: z.string(),
});

export const projectStatusSnapshotsSchema = z.object({
  available: z.boolean(),
  count: z.number(),
  latest_snapshot_id: z.string().nullable(),
  latest_snapshot_kind: z.string().nullable(),
});

export const projectStatusExportsSchema = z.object({
  available: z.boolean(),
  count: z.number(),
  latest_export_id: z.string().nullable(),
  latest_export_kind: z.string().nullable(),
  latest_export_format: z.string().nullable(),
});

export const projectWorkflowEventSchema = z.object({
  event_type: z.string(),
  status: z.string(),
  occurred_at: z.string(),
  story_id: z.string(),
  import_id: z.string(),
  run_id: z.string(),
  snapshot_id: z.string(),
  export_id: z.string(),
  summary: z.string(),
});

export const projectStatusSchema = z.object({
  project_id: z.string(),
  status: z.string(),
  story_count: z.number(),
  import_count: z.number(),
  run_count: z.number(),
  latest_import: projectStatusImportSchema.nullable(),
  latest_engine_run: projectStatusRunSchema.nullable(),
  worker: projectStatusWorkerSchema,
  snapshots: projectStatusSnapshotsSchema,
  exports: projectStatusExportsSchema,
  latest_failure_summary: z.string(),
  recent_workflow_events: z.array(projectWorkflowEventSchema),
});

export const projectOutputCanonSummarySchema = z.object({
  available: z.boolean(),
  title: z.string(),
  snapshot_kind: z.string(),
  created_at: z.string(),
  source_id: z.string(),
  chapters: z.number(),
  scenes: z.number(),
  evidence_anchor_count: z.number(),
  extraction_result_count: z.number(),
  accepted_entity_count: z.number(),
  accepted_fact_count: z.number(),
  accepted_relationship_count: z.number(),
  accepted_state_change_count: z.number(),
  rejected_candidate_count: z.number(),
  chapter_scene_counts: z.array(z.object({
    chapter_index: z.number(),
    scene_count: z.number(),
  })),
});

export const projectOutputSurfaceSchema = z.object({
  surface: z.string(),
  title: z.string(),
  status: z.string(),
  summary: z.string(),
  item_count: z.number(),
});

export const projectLanguageIdentitySummarySchema = z
  .object({
    translation_unit_count: z.number(),
    translation_review_count: z.number(),
    translation_review_items: z
      .array(
        z.object({
          issue_code: z.string(),
          issue_label: z.string(),
          chapter_id: z.string().default(""),
          scene_id: z.string().default(""),
          evidence_anchor_count: z.number(),
          reason: z.string().default(""),
        }),
      )
      .default([]),
    identity_decision_count: z.number(),
    identity_resolved_count: z.number(),
    identity_ambiguous_count: z.number(),
    identity_unresolved_count: z.number(),
    identity_review_items: z
      .array(
        z.object({
          status: z.string(),
          chapter_id: z.string().default(""),
          scene_id: z.string().default(""),
          evidence_anchor_id: z.string(),
          reference_kind: z.string().default("reference"),
          reference_label: z.string().default("Reference needing review"),
          candidate_count: z.number(),
          confidence: z.number(),
          reason: z.string().default(""),
        }),
      )
      .default([]),
  })
  .default({
    translation_unit_count: 0,
    translation_review_count: 0,
    translation_review_items: [],
    identity_decision_count: 0,
    identity_resolved_count: 0,
    identity_ambiguous_count: 0,
    identity_unresolved_count: 0,
    identity_review_items: [],
  });

export const projectTimelineChangeSchema = z.object({
  change_id: z.string(),
  chapter_index: z.number(),
  scene_index: z.number(),
  chapter_title: z.string(),
  scene_title: z.string(),
  entity_id: z.string(),
  entity_name: z.string(),
  attribute: z.string(),
  value: z.string(),
});

export const projectExportOptionSchema = z.object({
  export_kind: z.string(),
  formats: z.array(z.string()),
  label: z.string(),
});

export const projectExportSchema = z.object({
  export_id: z.string(),
  project_id: z.string(),
  snapshot_id: z.string(),
  export_kind: z.string(),
  export_format: z.string(),
  filename: z.string(),
  content_type: z.string(),
  size: z.number(),
  checksum: z.string(),
  created_at: z.string(),
});

export const projectExportListSchema = z.object({
  exports: z.array(projectExportSchema),
});

export const projectOutputsSchema = z.object({
  project_id: z.string(),
  status: z.string(),
  latest_import: projectStatusImportSchema.nullable(),
  latest_engine_run: projectStatusRunSchema.nullable(),
  canon: projectOutputCanonSummarySchema,
  surfaces: z.array(projectOutputSurfaceSchema),
  language_identity: projectLanguageIdentitySummarySchema,
  character_profiles: z.array(z.lazy(() => characterProfileSchema)),
  world_sheet: z.lazy(() => worldSheetSchema).nullable(),
  timeline_changes: z.array(projectTimelineChangeSchema).default([]),
  scene_sheets: z.array(z.lazy(() => sceneSheetSchema)).default([]),
  prompt_packs: z.array(z.lazy(() => productionPackSchema)).default([]),
  continuity_report: z.lazy(() => continuityReportSchema).nullable().default(null),
  export_options: z.array(projectExportOptionSchema).default([]),
});

export const snapshotSchema = z.object({
  snapshot_id: z.string(),
  project_id: z.string(),
  story_id: z.string(),
  run_id: z.string(),
  snapshot_kind: z.string(),
  content_type: z.string(),
  serialized_output: z.string(),
  created_at: z.string(),
});

export const snapshotListSchema = z.object({
  snapshots: z.array(snapshotSchema),
});

export const evidenceAnchorPreviewSchema = z.object({
  anchor_id: z.string(),
  chapter_id: z.string(),
  scene_id: z.string(),
  paragraph_index: z.number(),
  sentence_index: z.number(),
});

export const sceneMapEntrySchema = z.object({
  chapter_id: z.string(),
  chapter_index: z.number(),
  scene_id: z.string(),
  scene_index: z.number(),
  title: z.string(),
});

export const importInspectSchema = z.object({
  source_id: z.string(),
  source_format: z.string(),
  title: z.string(),
  chapters: z.number(),
  chapter_ids: z.array(z.string()),
  scenes: z.number(),
  scene_ids: z.array(z.string()),
  scene_map: z.array(sceneMapEntrySchema),
  paragraphs: z.number(),
  evidence_anchors: z.number(),
  first_evidence_anchors: z.array(evidenceAnchorPreviewSchema),
});

export const outputSectionSchema = z.object({
  title: z.string(),
  items: z.array(z.string()),
});

const unknownRaceSection = { title: "Race", items: ["Unknown"] };
const unknownGenderSection = { title: "Gender", items: ["Unknown"] };

export const characterProfileSchema = z
  .object({
    character_id: z.string(),
    display_name: z.string(),
    subtitle: z.string(),
    race: outputSectionSchema.optional(),
    gender: outputSectionSchema.optional(),
    status: outputSectionSchema,
    current_goal: outputSectionSchema,
    current_equipment: outputSectionSchema,
    current_abilities: outputSectionSchema,
    current_assets: outputSectionSchema,
    territory: outputSectionSchema,
    relationships: outputSectionSchema,
    current_limitations: outputSectionSchema,
    recent_changes: outputSectionSchema,
    evidence_summary: z.string(),
  })
  .transform((profile) => ({
    ...profile,
    race: profile.race ?? unknownRaceSection,
    gender: profile.gender ?? unknownGenderSection,
  }));

export const characterPreviewSchema = z.object({
  source_id: z.string(),
  source_format: z.string(),
  scene_id: z.string(),
  character_profiles: z.array(characterProfileSchema),
});

export const timelinePreviewSchema = z.object({
  source_id: z.string(),
  source_format: z.string(),
  current_scene_id: z.string(),
  chapter_ids: z.array(z.string()),
  scene_map: z.array(sceneMapEntrySchema),
  accepted_state_change_ids: z.array(z.string()),
});

export const sceneSheetSchema = z.object({
  scene_id: z.string(),
  title: z.string(),
  chapter_label: z.string(),
  location: outputSectionSchema,
  characters_present: outputSectionSchema,
  mood: outputSectionSchema,
  purpose: outputSectionSchema,
  visual_highlights: outputSectionSchema,
  continuity_changes: outputSectionSchema,
  environment: outputSectionSchema,
  evidence_summary: z.string(),
});

export const scenePreviewSchema = z.object({
  source_id: z.string(),
  source_format: z.string(),
  scene_id: z.string(),
  scene_sheet: sceneSheetSchema,
});

export const productionPackSchema = z.object({
  scene: sceneSheetSchema,
  image_prompt: outputSectionSchema,
  narration_prompt: outputSectionSchema,
  camera_prompt: outputSectionSchema,
  animation_prompt: outputSectionSchema,
});

export const promptPreviewSchema = z.object({
  source_id: z.string(),
  source_format: z.string(),
  scene_id: z.string(),
  production_pack: productionPackSchema,
});

export const exportPreviewSchema = z.object({
  source_id: z.string(),
  source_format: z.string(),
  scene_id: z.string(),
  export_kind: z.string(),
  export_format: z.string(),
  filename: z.string(),
  content_type: z.string(),
  content: z.string(),
});

export const continuityRecordSchema = z.object({
  record_id: z.string(),
  record_type: z.string(),
  description: z.string(),
  evidence_id: z.string(),
  chapter_id: z.string(),
  scene_id: z.string(),
});

export const continuitySceneSchema = z.object({
  scene_id: z.string(),
  new: z.array(continuityRecordSchema),
  updated: z.array(continuityRecordSchema),
  still_known: z.array(continuityRecordSchema),
  invalidated: z.array(continuityRecordSchema),
});

export const continuityReportSchema = z.object({
  source_id: z.string(),
  scenes: z.array(continuitySceneSchema),
});

export const continuityPreviewSchema = z.object({
  source_id: z.string(),
  source_format: z.string(),
  continuity_report: continuityReportSchema,
});

export const worldSheetSchema = z.object({
  chapter_label: z.string(),
  entity_sections: z.array(outputSectionSchema),
  evidence_summary: z.string(),
});

export const worldPreviewSchema = z.object({
  source_id: z.string(),
  source_format: z.string(),
  scene_id: z.string(),
  world_sheet: worldSheetSchema,
});

export type ApiHealth = z.infer<typeof healthSchema>;
export type ApiCapabilities = z.infer<typeof capabilitiesSchema>;
export type SourceFormats = z.infer<typeof sourceFormatsSchema>;
export type ImportInspect = z.infer<typeof importInspectSchema>;
export type SceneMapEntry = z.infer<typeof sceneMapEntrySchema>;
export type OutputSection = z.infer<typeof outputSectionSchema>;
export type CharacterProfile = z.infer<typeof characterProfileSchema>;
export type CharacterPreview = z.infer<typeof characterPreviewSchema>;
export type TimelinePreview = z.infer<typeof timelinePreviewSchema>;
export type SceneSheet = z.infer<typeof sceneSheetSchema>;
export type ScenePreview = z.infer<typeof scenePreviewSchema>;
export type ProductionPack = z.infer<typeof productionPackSchema>;
export type PromptPreview = z.infer<typeof promptPreviewSchema>;
export type ExportPreview = z.infer<typeof exportPreviewSchema>;
export type ContinuityRecord = z.infer<typeof continuityRecordSchema>;
export type ContinuityScene = z.infer<typeof continuitySceneSchema>;
export type ContinuityReport = z.infer<typeof continuityReportSchema>;
export type ContinuityPreview = z.infer<typeof continuityPreviewSchema>;
export type WorldSheet = z.infer<typeof worldSheetSchema>;
export type WorldPreview = z.infer<typeof worldPreviewSchema>;
export type AuthSession = z.infer<typeof authSessionSchema>;
export type AuthUser = z.infer<typeof authMeSchema>;
export type Project = z.infer<typeof projectSchema>;
export type ProjectList = z.infer<typeof projectListSchema>;
export type ProjectSettings = z.infer<typeof projectSettingsSchema>;
export type Story = z.infer<typeof storySchema>;
export type StoryList = z.infer<typeof storyListSchema>;
export type ImportRecord = z.infer<typeof importRecordSchema>;
export type ImportList = z.infer<typeof importListSchema>;
export type EngineRun = z.infer<typeof engineRunSchema>;
export type EngineRunList = z.infer<typeof engineRunListSchema>;
export type WorkerProcess = z.infer<typeof workerProcessSchema>;
export type ProjectStatus = z.infer<typeof projectStatusSchema>;
export type ProjectOutputCanonSummary = z.infer<typeof projectOutputCanonSummarySchema>;
export type ProjectOutputSurface = z.infer<typeof projectOutputSurfaceSchema>;
export type ProjectLanguageIdentitySummary = z.infer<
  typeof projectLanguageIdentitySummarySchema
>;
export type ProjectTimelineChange = z.infer<typeof projectTimelineChangeSchema>;
export type ProjectExportOption = z.infer<typeof projectExportOptionSchema>;
export type ProjectExport = z.infer<typeof projectExportSchema>;
export type ProjectExportList = z.infer<typeof projectExportListSchema>;
export type ProjectOutputs = z.infer<typeof projectOutputsSchema>;
export type Snapshot = z.infer<typeof snapshotSchema>;
export type SnapshotList = z.infer<typeof snapshotListSchema>;
