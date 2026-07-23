import { z } from "zod";

import {
  authMeSchema,
  authSessionSchema,
  capabilitiesSchema,
  characterPreviewSchema,
  continuityPreviewSchema,
  engineRunListSchema,
  engineRunSchema,
  exportPreviewSchema,
  projectExportListSchema,
  projectExportSchema,
  promptPreviewSchema,
  scenePreviewSchema,
  snapshotListSchema,
  storyListSchema,
  storySchema,
  timelinePreviewSchema,
  workerProcessSchema,
  worldPreviewSchema,
  healthSchema,
  importInspectSchema,
  importListSchema,
  importRecordSchema,
  projectListSchema,
  projectSettingsSchema,
  projectStatusSchema,
  projectOutputsSchema,
  projectSchema,
  sourceFormatsSchema,
  type ApiCapabilities,
  type ApiHealth,
  type AuthSession,
  type AuthUser,
  type CharacterPreview,
  type ContinuityPreview,
  type EngineRun,
  type EngineRunList,
  type ExportPreview,
  type PromptPreview,
  type ScenePreview,
  type SnapshotList,
  type TimelinePreview,
  type WorkerProcess,
  type WorldPreview,
  type ImportInspect,
  type ImportList,
  type ImportRecord,
  type Project,
  type ProjectList,
  type ProjectSettings,
  type ProjectStatus,
  type ProjectExport,
  type ProjectExportList,
  type ProjectOutputs,
  type Story,
  type StoryList,
  type SourceFormats,
} from "./schemas";

export const API_PATHS = {
  health: "/v2/health",
  capabilities: "/v2/capabilities",
  sourceFormats: "/v2/source-formats",
  importsInspect: "/v2/imports/inspect",
  charactersPreview: "/v2/characters/preview",
  continuityPreview: "/v2/continuity/preview",
  exportsPreview: "/v2/exports/preview",
  promptsPreview: "/v2/prompts/preview",
  scenesPreview: "/v2/scenes/preview",
  timelinePreview: "/v2/timeline/preview",
  worldPreview: "/v2/world/preview",
  authRegister: "/v2/auth/register",
  authLogin: "/v2/auth/login",
  authMe: "/v2/auth/me",
  projects: "/v2/projects",
  workerProcess: "/v2/workers/process",
} as const;

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(message: string, status: number, code: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

export type LoginRequest = {
  email: string;
  password: string;
  now: string;
};

export type RegisterRequest = LoginRequest & {
  user_id: string;
  display_name: string;
};

export type ProjectCreateRequest = {
  project_id: string;
  name: string;
  now: string;
};

export type ProjectSettingsRequest = {
  default_export_format: string;
  locale: string;
};

export type StoryCreateRequest = {
  story_id: string;
  title: string;
  now: string;
};

export type ImportInspectRequest = {
  source_id: string;
  filename: string;
  content_base64: string;
  title?: string;
};

export type ImportCreateRequest = ImportInspectRequest & {
  import_id: string;
  now: string;
};

export type EngineRunCreateRequest = {
  run_id: string;
  job_id: string;
  now: string;
};

export type WorkerProcessRequest = {
  started_at: string;
  finished_at: string;
  max_jobs: number;
};

export type CharacterPreviewRequest = ImportInspectRequest & {
  ai_response: unknown;
  character_ids?: string[];
  scene_id?: string;
};

export type TimelinePreviewRequest = ImportInspectRequest & {
  ai_response: unknown;
  scene_id?: string;
};

export type ScenePreviewRequest = ImportInspectRequest & {
  ai_response: unknown;
  character_ids?: string[];
  scene_id?: string;
};

export type PromptPreviewRequest = ImportInspectRequest & {
  ai_response: unknown;
  character_ids?: string[];
  scene_id?: string;
};

export type ContinuityPreviewRequest = ImportInspectRequest & {
  ai_response: unknown;
  scene_id?: string;
};

export type WorldPreviewRequest = ImportInspectRequest & {
  ai_response: unknown;
  world_entity_ids?: string[];
  scene_id?: string;
};

export type ExportPreviewRequest = ImportInspectRequest & {
  ai_response: unknown;
  export_kind: string;
  export_format: string;
  character_ids?: string[];
  scene_id?: string;
  world_entity_ids?: string[];
};

export type ProjectExportCreateRequest = {
  export_id: string;
  snapshot_id: string;
  export_format: string;
  filename?: string;
  now: string;
};

export type ExportDownload = {
  blob: Blob;
  filename: string;
  contentType: string;
};

export type JsonPostResponse = {
  ok: boolean;
  status: number;
  payload: unknown;
};

export async function postJson(
  url: string,
  {
    headers,
    body,
    method = "POST",
  }: {
    headers: HeadersInit;
    body: unknown;
    method?: "POST" | "PUT";
  },
): Promise<JsonPostResponse> {
  let response: Response;
  try {
    response = await fetch(url, {
      method,
      headers,
      body: JSON.stringify(body),
    });
  } catch (error) {
    throw new ApiError(friendlyNetworkMessage(error), 0, "network_error");
  }

  return {
    ok: response.ok,
    status: response.status,
    payload: await readOptionalJsonPayload(response),
  };
}

export class AevrynApiClient {
  readonly baseUrl: string;

  constructor(baseUrl: string = import.meta.env.VITE_AEVRYN_API_URL ?? "") {
    this.baseUrl = baseUrl.replace(/\/$/, "");
  }

  health(): Promise<ApiHealth> {
    return this.request(API_PATHS.health, healthSchema);
  }

  capabilities(): Promise<ApiCapabilities> {
    return this.request(API_PATHS.capabilities, capabilitiesSchema);
  }

  sourceFormats(): Promise<SourceFormats> {
    return this.request(API_PATHS.sourceFormats, sourceFormatsSchema);
  }

  inspectImport(
    payload: ImportInspectRequest,
    sessionToken?: string,
    now?: string,
  ): Promise<ImportInspect> {
    return this.request(API_PATHS.importsInspect, importInspectSchema, {
      method: "POST",
      headers: sessionToken && now ? authHeaders(sessionToken, now) : undefined,
      body: JSON.stringify(payload),
    });
  }

  previewCharacters(payload: CharacterPreviewRequest): Promise<CharacterPreview> {
    return this.request(API_PATHS.charactersPreview, characterPreviewSchema, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  previewTimeline(payload: TimelinePreviewRequest): Promise<TimelinePreview> {
    return this.request(API_PATHS.timelinePreview, timelinePreviewSchema, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  previewScene(payload: ScenePreviewRequest): Promise<ScenePreview> {
    return this.request(API_PATHS.scenesPreview, scenePreviewSchema, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  previewPrompts(payload: PromptPreviewRequest): Promise<PromptPreview> {
    return this.request(API_PATHS.promptsPreview, promptPreviewSchema, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  previewContinuity(payload: ContinuityPreviewRequest): Promise<ContinuityPreview> {
    return this.request(API_PATHS.continuityPreview, continuityPreviewSchema, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  previewWorld(payload: WorldPreviewRequest): Promise<WorldPreview> {
    return this.request(API_PATHS.worldPreview, worldPreviewSchema, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  previewExport(payload: ExportPreviewRequest): Promise<ExportPreview> {
    return this.request(API_PATHS.exportsPreview, exportPreviewSchema, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  register(payload: RegisterRequest): Promise<AuthSession> {
    return this.request(API_PATHS.authRegister, authSessionSchema, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  login(payload: LoginRequest): Promise<AuthSession> {
    return this.request(API_PATHS.authLogin, authSessionSchema, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  me(sessionToken: string, now: string): Promise<AuthUser> {
    return this.request(API_PATHS.authMe, authMeSchema, {
      headers: {
        Authorization: `Bearer ${sessionToken}`,
        "X-Aevryn-Now": now,
      },
    });
  }

  listProjects(sessionToken: string, now: string): Promise<ProjectList> {
    return this.request(API_PATHS.projects, projectListSchema, {
      headers: authHeaders(sessionToken, now),
    });
  }

  createProject(
    payload: ProjectCreateRequest,
    sessionToken: string,
    now: string,
  ): Promise<Project> {
    return this.request(API_PATHS.projects, projectSchema, {
      method: "POST",
      headers: authHeaders(sessionToken, now),
      body: JSON.stringify(payload),
    });
  }

  getProject(projectId: string, sessionToken: string, now: string): Promise<Project> {
    return this.request(projectPath(projectId), projectSchema, {
      headers: authHeaders(sessionToken, now),
    });
  }

  async deleteProject(projectId: string, sessionToken: string, now: string): Promise<void> {
    await this.requestNoContent(projectPath(projectId), {
      method: "DELETE",
      headers: authHeaders(sessionToken, now),
    });
  }

  getProjectSettings(
    projectId: string,
    sessionToken: string,
    now: string,
  ): Promise<ProjectSettings> {
    return this.request(projectSettingsPath(projectId), projectSettingsSchema, {
      headers: authHeaders(sessionToken, now),
    });
  }

  updateProjectSettings(
    projectId: string,
    payload: ProjectSettingsRequest,
    sessionToken: string,
    now: string,
  ): Promise<ProjectSettings> {
    return this.request(projectSettingsPath(projectId), projectSettingsSchema, {
      method: "PUT",
      headers: authHeaders(sessionToken, now),
      body: JSON.stringify(payload),
    });
  }

  listStories(projectId: string, sessionToken: string, now: string): Promise<StoryList> {
    return this.request(projectStoriesPath(projectId), storyListSchema, {
      headers: authHeaders(sessionToken, now),
    });
  }

  createStory(
    projectId: string,
    payload: StoryCreateRequest,
    sessionToken: string,
    now: string,
  ): Promise<Story> {
    return this.request(projectStoriesPath(projectId), storySchema, {
      method: "POST",
      headers: authHeaders(sessionToken, now),
      body: JSON.stringify(payload),
    });
  }

  async deleteStory(
    projectId: string,
    storyId: string,
    sessionToken: string,
    now: string,
  ): Promise<void> {
    await this.requestNoContent(projectStoryPath(projectId, storyId), {
      method: "DELETE",
      headers: authHeaders(sessionToken, now),
    });
  }

  listStoryImports(
    projectId: string,
    storyId: string,
    sessionToken: string,
    now: string,
  ): Promise<ImportList> {
    return this.request(projectStoryImportsPath(projectId, storyId), importListSchema, {
      headers: authHeaders(sessionToken, now),
    });
  }

  createStoryImport(
    projectId: string,
    storyId: string,
    payload: ImportCreateRequest,
    sessionToken: string,
    now: string,
  ): Promise<ImportRecord> {
    return this.request(projectStoryImportsPath(projectId, storyId), importRecordSchema, {
      method: "POST",
      headers: authHeaders(sessionToken, now),
      body: JSON.stringify(payload),
    });
  }

  listProjectRuns(projectId: string, sessionToken: string, now: string): Promise<EngineRunList> {
    return this.request(projectRunsPath(projectId), engineRunListSchema, {
      headers: authHeaders(sessionToken, now),
    });
  }

  projectStatus(projectId: string, sessionToken: string, now: string): Promise<ProjectStatus> {
    return this.request(projectStatusPath(projectId), projectStatusSchema, {
      headers: authHeaders(sessionToken, now),
    });
  }

  projectOutputs(projectId: string, sessionToken: string, now: string): Promise<ProjectOutputs> {
    return this.request(projectOutputsPath(projectId), projectOutputsSchema, {
      headers: authHeaders(sessionToken, now),
    });
  }

  listProjectExports(
    projectId: string,
    sessionToken: string,
    now: string,
  ): Promise<ProjectExportList> {
    return this.request(projectExportsPath(projectId), projectExportListSchema, {
      headers: authHeaders(sessionToken, now),
    });
  }

  createProjectExport(
    projectId: string,
    payload: ProjectExportCreateRequest,
    sessionToken: string,
    now: string,
  ): Promise<ProjectExport> {
    return this.request(projectExportsPath(projectId), projectExportSchema, {
      method: "POST",
      headers: authHeaders(sessionToken, now),
      body: JSON.stringify(payload),
    });
  }

  async downloadProjectExport(
    projectId: string,
    exportId: string,
    sessionToken: string,
    now: string,
  ): Promise<ExportDownload> {
    const response = await this.requestBlob(projectExportDownloadPath(projectId, exportId), {
      headers: authHeaders(sessionToken, now),
    });
    return response;
  }

  listProjectSnapshots(
    projectId: string,
    sessionToken: string,
    now: string,
  ): Promise<SnapshotList> {
    return this.request(projectSnapshotsPath(projectId), snapshotListSchema, {
      headers: authHeaders(sessionToken, now),
    });
  }

  listStorySnapshots(
    projectId: string,
    storyId: string,
    sessionToken: string,
    now: string,
    snapshotKind?: string,
  ): Promise<SnapshotList> {
    return this.request(storySnapshotsPath(projectId, storyId, snapshotKind), snapshotListSchema, {
      headers: authHeaders(sessionToken, now),
    });
  }

  submitImportRun(
    projectId: string,
    storyId: string,
    importId: string,
    payload: EngineRunCreateRequest,
    sessionToken: string,
    now: string,
  ): Promise<EngineRun> {
    return this.request(projectImportRunsPath(projectId, storyId, importId), engineRunSchema, {
      method: "POST",
      headers: authHeaders(sessionToken, now),
      body: JSON.stringify(payload),
    });
  }

  processWorkerJobs(payload: WorkerProcessRequest): Promise<WorkerProcess> {
    return this.request(API_PATHS.workerProcess, workerProcessSchema, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  private async request<TSchema extends z.ZodTypeAny>(
    path: string,
    schema: TSchema,
    init: RequestInit = {},
  ): Promise<z.output<TSchema>> {
    const headers = new Headers(init.headers);
    headers.set("Accept", "application/json");
    if (init.body) {
      headers.set("Content-Type", "application/json");
    }

    let response: Response;
    try {
      response = await fetch(`${this.baseUrl}${path}`, { ...init, headers });
    } catch (error) {
      throw new ApiError(friendlyNetworkMessage(error), 0, "network_error");
    }

    const payload = await readJsonPayload(response);
    if (!response.ok) {
      const errorPayload = z
        .object({ error: z.string().optional(), detail: z.string().optional() })
        .safeParse(payload);
      throw new ApiError(
        errorPayload.data?.detail ?? "Aevryn API request failed.",
        response.status,
        errorPayload.data?.error ?? "request_failed",
      );
    }

    const parsed = schema.safeParse(payload);
    if (!parsed.success) {
      throw new ApiError(
        "Aevryn API returned an unexpected response shape.",
        response.status,
        "invalid_response",
      );
    }
    return parsed.data;
  }

  private async requestNoContent(path: string, init: RequestInit = {}): Promise<void> {
    const headers = new Headers(init.headers);
    headers.set("Accept", "application/json");

    let response: Response;
    try {
      response = await fetch(`${this.baseUrl}${path}`, { ...init, headers });
    } catch (error) {
      throw new ApiError(friendlyNetworkMessage(error), 0, "network_error");
    }

    if (!response.ok) {
      const payload = await readJsonPayload(response);
      const errorPayload = z
        .object({ error: z.string().optional(), detail: z.string().optional() })
        .safeParse(payload);
      throw new ApiError(
        errorPayload.data?.detail ?? "Aevryn API request failed.",
        response.status,
        errorPayload.data?.error ?? "request_failed",
      );
    }
  }

  private async requestBlob(path: string, init: RequestInit = {}): Promise<ExportDownload> {
    const headers = new Headers(init.headers);
    let response: Response;
    try {
      response = await fetch(`${this.baseUrl}${path}`, { ...init, headers });
    } catch (error) {
      throw new ApiError(friendlyNetworkMessage(error), 0, "network_error");
    }

    if (!response.ok) {
      const payload = await readJsonPayload(response);
      const errorPayload = z
        .object({ error: z.string().optional(), detail: z.string().optional() })
        .safeParse(payload);
      throw new ApiError(
        errorPayload.data?.detail ?? "Aevryn API request failed.",
        response.status,
        errorPayload.data?.error ?? "request_failed",
      );
    }

    return {
      blob: await response.blob(),
      filename: filenameFromContentDisposition(response.headers.get("Content-Disposition")),
      contentType: response.headers.get("Content-Type") ?? "application/octet-stream",
    };
  }
}

function authHeaders(sessionToken: string, now: string): HeadersInit {
  return {
    Authorization: `Bearer ${sessionToken}`,
    "X-Aevryn-Now": now,
  };
}

function projectSettingsPath(projectId: string): string {
  return `${projectPath(projectId)}/settings`;
}

function projectPath(projectId: string): string {
  return `${API_PATHS.projects}/${encodeURIComponent(projectId)}`;
}

function projectStoriesPath(projectId: string): string {
  return `${API_PATHS.projects}/${encodeURIComponent(projectId)}/stories`;
}

function projectStoryPath(projectId: string, storyId: string): string {
  return `${projectStoriesPath(projectId)}/${encodeURIComponent(storyId)}`;
}

function projectStoryImportsPath(projectId: string, storyId: string): string {
  return `${projectStoryPath(projectId, storyId)}/imports`;
}

function projectRunsPath(projectId: string): string {
  return `${API_PATHS.projects}/${encodeURIComponent(projectId)}/runs`;
}

function projectStatusPath(projectId: string): string {
  return `${API_PATHS.projects}/${encodeURIComponent(projectId)}/status`;
}

function projectOutputsPath(projectId: string): string {
  return `${API_PATHS.projects}/${encodeURIComponent(projectId)}/outputs`;
}

function projectExportsPath(projectId: string): string {
  return `${API_PATHS.projects}/${encodeURIComponent(projectId)}/exports`;
}

function projectExportDownloadPath(projectId: string, exportId: string): string {
  return `${projectExportsPath(projectId)}/${encodeURIComponent(exportId)}/download`;
}

function projectSnapshotsPath(projectId: string): string {
  return `${API_PATHS.projects}/${encodeURIComponent(projectId)}/snapshots`;
}

function storySnapshotsPath(projectId: string, storyId: string, snapshotKind?: string): string {
  const path = `${projectStoryPath(projectId, storyId)}/snapshots`;
  if (!snapshotKind) {
    return path;
  }
  return `${path}?snapshot_kind=${encodeURIComponent(snapshotKind)}`;
}

function projectImportRunsPath(projectId: string, storyId: string, importId: string): string {
  return `${projectStoryImportsPath(projectId, storyId)}/${encodeURIComponent(importId)}/runs`;
}

function filenameFromContentDisposition(value: string | null): string {
  if (!value) {
    return "aevryn-export";
  }
  const match = value.match(/filename="([^"]+)"/u) ?? value.match(/filename=([^;]+)/u);
  return match?.[1]?.trim() || "aevryn-export";
}

async function readJsonPayload(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    if (response.ok) {
      throw new ApiError("Aevryn API returned invalid JSON.", response.status, "invalid_json");
    }
    return {};
  }
}

async function readOptionalJsonPayload(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return {};
  }
}

function messageFromUnknown(error: unknown, fallback: string): string {
  return error instanceof Error && error.message ? error.message : fallback;
}

function friendlyNetworkMessage(error: unknown): string {
  const message = messageFromUnknown(error, "Aevryn API is unreachable.");
  if (message.toLowerCase() === "failed to fetch") {
    return "Aevryn API is unreachable. Try again, then check service status if it continues.";
  }
  return message;
}

export const apiClient = new AevrynApiClient();
