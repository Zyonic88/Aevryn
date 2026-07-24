import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";

import { apiClient, type ExportPreviewRequest } from "../api/client";
import type { ExportPreview, ProjectExport, ProjectExportList } from "../api/schemas";
import { useAuth } from "../auth/useAuth";
import { EmptyState, ErrorMessage, LoadingMessage } from "../components/Feedback";
import { formatDateTime } from "../formatting/display";
import {
  DeveloperPreviewToggle,
  ProjectOutputSummaryPanel,
} from "../output/ProjectOutputSummaryPanel";
import {
  buildExportPreviewPayload,
  canSubmitExportPreviewInput,
} from "../previewing/previewPayload";
import type { ProjectSummary } from "../projects/projectStore";

const exportOptions = [
  { kind: "character_profile", format: "markdown", label: "Character Profile / Markdown" },
  { kind: "scene_sheet", format: "markdown", label: "Scene Sheet / Markdown" },
  { kind: "production_pack", format: "markdown", label: "Production Pack / Markdown" },
  { kind: "world_sheet", format: "markdown", label: "World Sheet / Markdown" },
  { kind: "prompt_bundle", format: "markdown", label: "Prompt Bundle / Markdown" },
  { kind: "prompt_bundle", format: "json", label: "Prompt Bundle / JSON" },
  { kind: "prompt_bundle", format: "csv", label: "Prompt Bundle / CSV" },
  { kind: "continuity_report", format: "markdown", label: "Continuity Report / Markdown" },
  { kind: "continuity_report", format: "json", label: "Continuity Report / JSON" },
] as const;

export function ExportWorkspaceView({ project }: { project: ProjectSummary }) {
  const { session } = useAuth();
  const queryClient = useQueryClient();
  const [sourceId, setSourceId] = useState(project.id.replace(/^project_/, "source_"));
  const [filename, setFilename] = useState("chapter_001.txt");
  const [title, setTitle] = useState(project.name);
  const [sourceText, setSourceText] = useState("");
  const [aiResponseText, setAiResponseText] = useState("");
  const [characterIdsText, setCharacterIdsText] = useState("");
  const [worldEntityIdsText, setWorldEntityIdsText] = useState("");
  const [sceneId, setSceneId] = useState("");
  const [selectedExport, setSelectedExport] = useState(optionValue(exportOptions[0]));
  const [formError, setFormError] = useState<string | null>(null);
  const [previewResult, setPreviewResult] = useState<ExportPreview | null>(null);
  const [createdExportId, setCreatedExportId] = useState<string | null>(null);
  const [downloadedExportName, setDownloadedExportName] = useState<string | null>(null);

  const activeExport = parseOptionValue(selectedExport);
  const statusQuery = useQuery({
    queryKey: ["project-status", project.id, session?.session_token],
    queryFn: () =>
      apiClient.projectStatus(
        project.id,
        requireSessionToken(session),
        new Date().toISOString(),
      ),
    enabled: session !== null,
  });
  const exportsQuery = useQuery({
    queryKey: projectExportsQueryKey(project.id, session?.session_token),
    queryFn: () =>
      apiClient.listProjectExports(
        project.id,
        requireSessionToken(session),
        new Date().toISOString(),
      ),
    enabled: session !== null,
  });
  const createSnapshotExport = useMutation({
    mutationFn: () => {
      const now = new Date().toISOString();
      return apiClient.createProjectExport(
        project.id,
        {
          export_id: newExportId(),
          snapshot_id: requireLatestSnapshotId(statusQuery.data?.snapshots.latest_snapshot_id),
          export_format: "json",
          filename: `${safeFilename(project.name)}-canon-snapshot.json`,
          now,
        },
        requireSessionToken(session),
        now,
      );
    },
    onSuccess(result) {
      setCreatedExportId(result.export_id);
      setDownloadedExportName(null);
      queryClient.setQueryData<ProjectExportList>(
        projectExportsQueryKey(project.id, session?.session_token),
        (current) => mergeProjectExportList(current, result),
      );
      void queryClient.invalidateQueries({
        queryKey: projectExportsQueryKey(project.id, session?.session_token),
      });
      void queryClient.invalidateQueries({
        queryKey: ["project-status", project.id, session?.session_token],
      });
    },
  });
  const downloadExport = useMutation({
    mutationFn: (exportRecord: ProjectExport) =>
      downloadProjectExport(project.id, exportRecord, requireSessionToken(session)),
    onMutate() {
      setDownloadedExportName(null);
    },
    onSuccess(_result, exportRecord) {
      setDownloadedExportName(exportRecord.filename);
    },
  });
  const previewExport = useMutation({
    mutationFn: (payload: ExportPreviewRequest) => apiClient.previewExport(payload),
    onSuccess(result) {
      setPreviewResult(result);
    },
    onError() {
      setPreviewResult(null);
    },
  });

  const canSubmit = canSubmitExportPreviewInput({
    sourceId,
    filename,
    title,
    sourceText,
    aiResponseText,
    characterIdsText,
    exportFormat: activeExport.format,
    exportKind: activeExport.kind,
    sceneId,
    worldEntityIdsText,
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    previewExport.reset();
    try {
      const payload = buildExportPreviewPayload({
        sourceId,
        filename,
        title,
        sourceText,
        aiResponseText,
        characterIdsText,
        exportFormat: activeExport.format,
        exportKind: activeExport.kind,
        sceneId,
        worldEntityIdsText,
      });
      setFormError(null);
      setPreviewResult(null);
      previewExport.mutate(payload);
    } catch (error) {
      setPreviewResult(null);
      setFormError(error instanceof Error ? error.message : "Export preview form is invalid.");
    }
  }

  return (
    <div className="workspace-view-stack">
      <div>
        <p className="eyebrow">Exports</p>
        <h2>Exports</h2>
      </div>

      <ProjectOutputSummaryPanel project={project} surface="exports" />

      <ProjectStoredExportsPanel
        exports={exportsQuery.data?.exports ?? []}
        exportsError={exportsQuery.error}
        isCreatePending={createSnapshotExport.isPending}
        downloadingExportId={
          downloadExport.isPending ? (downloadExport.variables?.export_id ?? null) : null
        }
        isLoading={statusQuery.isLoading || exportsQuery.isLoading}
        latestSnapshotId={statusQuery.data?.snapshots.latest_snapshot_id ?? ""}
        mutationError={createSnapshotExport.error ?? downloadExport.error}
        onCreateSnapshotExport={() => createSnapshotExport.mutate()}
        onDownload={(exportRecord) => downloadExport.mutate(exportRecord)}
        statusError={statusQuery.error}
        createdExportId={createdExportId}
        downloadedExportName={downloadedExportName}
      />

      <DeveloperPreviewToggle>
        <section>
          <h2>Export Preview</h2>
          <p className="field-note">
            Technical review requires real source text and extraction JSON. It does not run with
            simulated source, placeholder AI output, or empty success paths.
          </p>
          <form className="import-form" onSubmit={submit}>
          <div className="form-row-grid">
            <label>
              Source reference
              <input value={sourceId} onChange={(event) => setSourceId(event.target.value)} />
            </label>
            <label>
              Filename
              <input value={filename} onChange={(event) => setFilename(event.target.value)} />
            </label>
          </div>
          <label>
            Export
            <select
              value={selectedExport}
              onChange={(event) => setSelectedExport(event.target.value)}
            >
              {exportOptions.map((option) => (
                <option key={optionValue(option)} value={optionValue(option)}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            Title
            <input value={title} onChange={(event) => setTitle(event.target.value)} />
          </label>
          <label>
            Source text
            <textarea
              value={sourceText}
              onChange={(event) => setSourceText(event.target.value)}
              required
              rows={8}
            />
          </label>
          <label>
            AI response JSON
            <textarea
              value={aiResponseText}
              onChange={(event) => setAiResponseText(event.target.value)}
              required
              rows={8}
            />
          </label>
          <div className="form-row-grid">
            <label>
              Character IDs
              <input
                value={characterIdsText}
                onChange={(event) => setCharacterIdsText(event.target.value)}
                placeholder="Optional: character_mark character_luna"
              />
            </label>
            <label>
              World Entity IDs
              <input
                value={worldEntityIdsText}
                onChange={(event) => setWorldEntityIdsText(event.target.value)}
                placeholder="Optional: location_hangar item_sword"
              />
            </label>
          </div>
          <label>
            Scene ID
            <input
              value={sceneId}
              onChange={(event) => setSceneId(event.target.value)}
              placeholder="Optional scene ID"
            />
          </label>
          {formError ? <ErrorMessage>{formError}</ErrorMessage> : null}
          {previewExport.error ? <ErrorMessage>{previewExport.error.message}</ErrorMessage> : null}
          <button
            type="submit"
            className="primary-button"
            disabled={!canSubmit || previewExport.isPending}
          >
            {previewExport.isPending ? "Building preview" : "Preview export"}
          </button>
          </form>
        </section>
      </DeveloperPreviewToggle>

      {previewResult ? <ExportPreviewResult result={previewResult} /> : null}
    </div>
  );
}

function ProjectStoredExportsPanel({
  exports,
  exportsError,
  isCreatePending,
  downloadingExportId,
  isLoading,
  latestSnapshotId,
  mutationError,
  onCreateSnapshotExport,
  onDownload,
  statusError,
  createdExportId,
  downloadedExportName,
}: {
  exports: ProjectExport[];
  exportsError: Error | null;
  isCreatePending: boolean;
  downloadingExportId: string | null;
  isLoading: boolean;
  latestSnapshotId: string;
  mutationError: Error | null;
  onCreateSnapshotExport: () => void;
  onDownload: (exportRecord: ProjectExport) => void;
  statusError: Error | null;
  createdExportId: string | null;
  downloadedExportName: string | null;
}) {
  const sortedExports = [...exports].sort((left, right) =>
    right.created_at.localeCompare(left.created_at),
  );
  const isDownloadPending = downloadingExportId !== null;
  const downloadingExport = exports.find(
    (exportRecord) => exportRecord.export_id === downloadingExportId,
  );

  return (
    <section className="project-panel" aria-label="Stored exports">
      <div className="panel-heading-row">
        <div>
          <h2>Stored Exports</h2>
          <p className="field-note">
            Create a downloadable JSON export from the latest accepted Canon snapshot.
          </p>
        </div>
        <button
          type="button"
          className="ghost-button"
          disabled={!latestSnapshotId || isCreatePending}
          onClick={onCreateSnapshotExport}
        >
          {isCreatePending ? "Creating export" : "Create snapshot export"}
        </button>
      </div>

      <dl className="settings-summary-list export-safety-summary" aria-label="Export behavior">
        <div>
          <dt>Snapshot source</dt>
          <dd>
            {latestSnapshotId ? "Latest accepted Canon snapshot" : "Waiting for processed Canon"}
          </dd>
        </div>
        <div>
          <dt>Beta export</dt>
          <dd>Canon Snapshot / JSON</dd>
        </div>
        <div>
          <dt>Access</dt>
          <dd>Authenticated download only</dd>
        </div>
        <div>
          <dt>Storage</dt>
          <dd>Private storage reference hidden</dd>
        </div>
      </dl>

      {isLoading ? <LoadingMessage>Loading stored exports.</LoadingMessage> : null}
      {statusError ? <ErrorMessage>{statusError.message}</ErrorMessage> : null}
      {exportsError ? <ErrorMessage>{exportsError.message}</ErrorMessage> : null}
      {mutationError ? <ErrorMessage>{mutationError.message}</ErrorMessage> : null}
      {createdExportId ? <p className="success-note">Snapshot export created.</p> : null}
      {isDownloadPending ? (
        <p className="success-note" role="status">
          Preparing authenticated download
          {downloadingExport ? ` for ${downloadingExport.filename}` : ""}.
        </p>
      ) : null}
      {downloadedExportName ? (
        <p className="success-note" role="status">
          Download prepared for {downloadedExportName}.
        </p>
      ) : null}
      {!latestSnapshotId && !isLoading ? (
        <EmptyState title="No snapshot ready">
          Process an import before creating a stored export.
        </EmptyState>
      ) : null}

      {sortedExports.length > 0 ? (
        <div className="export-list">
          {sortedExports.map((exportRecord) => (
            <article className="export-list-item" key={exportRecord.export_id}>
              <div>
                <h3>{exportRecord.filename}</h3>
                <p>
                  {readableExportKind(exportRecord.export_kind)} /{" "}
                  {readableExportFormat(exportRecord.export_format)} |{" "}
                  {formatBytes(exportRecord.size)} | {formatDateTime(exportRecord.created_at)}
                </p>
              </div>
              <button
                type="button"
                className="ghost-button"
                disabled={isDownloadPending}
                onClick={() => onDownload(exportRecord)}
              >
                {downloadingExportId === exportRecord.export_id ? "Preparing" : "Download"}
              </button>
            </article>
          ))}
        </div>
      ) : latestSnapshotId && !isLoading ? (
        <EmptyState title="No exports yet">
          Create a snapshot export to save a downloadable copy.
        </EmptyState>
      ) : null}
    </section>
  );
}

function ExportPreviewResult({ result }: { result: ExportPreview }) {
  const contentSummary = `${result.content.length.toLocaleString()} character${
    result.content.length === 1 ? "" : "s"
  }`;

  return (
    <section className="project-panel" aria-label="Export preview result">
      <h2>{result.filename}</h2>
      <dl className="metric-grid export-metadata">
        <div>
          <dt>Kind</dt>
          <dd>{readableExportKind(result.export_kind)}</dd>
        </div>
        <div>
          <dt>Format</dt>
          <dd>{readableExportFormat(result.export_format)}</dd>
        </div>
        <div>
          <dt>Content Type</dt>
          <dd>{result.content_type}</dd>
        </div>
      </dl>
      <details className="detail-disclosure export-preview-disclosure">
        <summary>Show export content - {contentSummary}</summary>
        <pre className="export-preview-content">{result.content}</pre>
      </details>
    </section>
  );
}

function optionValue(option: { kind: string; format: string }): string {
  return `${option.kind}:${option.format}`;
}

function parseOptionValue(value: string): { kind: string; format: string } {
  const [kind = "", format = ""] = value.split(":");
  return { kind, format };
}

function projectExportsQueryKey(projectId: string, sessionToken: string | undefined) {
  return ["project-exports", projectId, sessionToken];
}

function mergeProjectExportList(
  current: ProjectExportList | undefined,
  createdExport: ProjectExport,
): ProjectExportList {
  const existingExports = current?.exports ?? [];
  return {
    exports: [
      createdExport,
      ...existingExports.filter((exportRecord) => exportRecord.export_id !== createdExport.export_id),
    ],
  };
}

function requireSessionToken(session: { session_token: string } | null): string {
  if (!session) {
    throw new Error("Login is required.");
  }
  return session.session_token;
}

function requireLatestSnapshotId(snapshotId: string | null | undefined): string {
  if (!snapshotId) {
    throw new Error("Process an import before creating an export.");
  }
  return snapshotId;
}

function safeFilename(value: string): string {
  const cleaned = value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/gu, "-")
    .replace(/^-+|-+$/gu, "");
  return cleaned || "aevryn-project";
}

function readableExportKind(value: string): string {
  const labels: Record<string, string> = {
    canon: "Canon Snapshot",
    character_profile: "Character Profile",
    continuity_report: "Continuity Report",
    production_pack: "Production Pack",
    prompt_bundle: "Prompt Bundle",
    scene_sheet: "Scene Sheet",
    world_sheet: "World Sheet",
  };
  return labels[value] ?? readableExportToken(value);
}

function readableExportFormat(value: string): string {
  const labels: Record<string, string> = {
    csv: "CSV",
    json: "JSON",
    markdown: "Markdown",
  };
  return labels[value] ?? readableExportToken(value);
}

function readableExportToken(value: string): string {
  return value
    .split("_")
    .filter(Boolean)
    .map((word) => `${word.charAt(0).toUpperCase()}${word.slice(1)}`)
    .join(" ");
}

function newExportId(): string {
  return `export_${crypto.randomUUID().replaceAll("-", "_")}`;
}

async function downloadProjectExport(
  projectId: string,
  exportRecord: ProjectExport,
  sessionToken: string,
): Promise<string> {
  const result = await apiClient.downloadProjectExport(
    projectId,
    exportRecord.export_id,
    sessionToken,
    new Date().toISOString(),
  );
  const url = URL.createObjectURL(result.blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = result.filename === "aevryn-export" ? exportRecord.filename : result.filename;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
  return exportRecord.export_id;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}
