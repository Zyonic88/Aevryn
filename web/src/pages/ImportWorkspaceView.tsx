import { useMutation, useQuery, useQueryClient, type QueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { NavLink } from "react-router-dom";

import { apiClient, type ImportInspectRequest } from "../api/client";
import { useAuth } from "../auth/useAuth";
import { EmptyState, ErrorMessage, LoadingMessage, StatusPanel } from "../components/Feedback";
import {
  MAX_IMPORT_SOURCE_CHARACTERS,
  buildImportInspectPayload,
  canBuildImportInspectPayload,
  encodeBytesBase64,
  encodeUtf8Base64,
  importSourceCharacterCountLabel,
  sourceIdFromFilename,
} from "../importing/importPayload";
import { formatRunStatus } from "../formatting/display";
import { importResultTotalsLabel, importScenePreviewRows } from "../importing/importResult";
import type { EngineRun, ImportInspect, ImportRecord, Snapshot, Story } from "../api/schemas";
import type { SourceFormats } from "../api/schemas";
import type { ProjectSummary } from "../projects/projectStore";
import { readActiveStoryId, saveActiveStoryId } from "../stories/activeStory";

const DEFAULT_IMPORT_TEXT = "";

export function ImportWorkspaceView({ project }: { project: ProjectSummary }) {
  const { session } = useAuth();
  const queryClient = useQueryClient();
  const [selectedStoryId, setSelectedStoryId] = useState(() => readActiveStoryId(project.id));
  const [importId, setImportId] = useState(project.id.replace(/^project_/, "import_"));
  const [sourceId, setSourceId] = useState(project.id.replace(/^project_/, "source_"));
  const [filename, setFilename] = useState("chapter_001.txt");
  const [title, setTitle] = useState(project.name);
  const [sourceText, setSourceText] = useState(DEFAULT_IMPORT_TEXT);
  const [fileContentBase64, setFileContentBase64] = useState("");
  const [selectedFileName, setSelectedFileName] = useState("");
  const [selectedFileSize, setSelectedFileSize] = useState(0);
  const [isReadingSourceFile, setIsReadingSourceFile] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [inspectionResult, setInspectionResult] = useState<ImportInspect | null>(null);

  const sourceFormats = useQuery({
    queryKey: ["source-formats"],
    queryFn: () => apiClient.sourceFormats(),
  });
  const storiesQuery = useQuery({
    queryKey: ["project-stories", project.id, session?.session_token],
    queryFn: () =>
      apiClient.listStories(project.id, requireSessionToken(session), new Date().toISOString()),
    enabled: session !== null,
  });
  const storyOptions = storiesQuery.data?.stories ?? [];
  const activeStoryId = storyOptions.some((story) => story.story_id === selectedStoryId)
    ? selectedStoryId
    : (storyOptions[0]?.story_id ?? "");
  const importsQuery = useQuery({
    queryKey: importQueryKey(project.id, activeStoryId, session?.session_token),
    queryFn: () =>
      apiClient.listStoryImports(
        project.id,
        activeStoryId,
        requireSessionToken(session),
        new Date().toISOString(),
      ),
    enabled: session !== null && activeStoryId !== "",
  });
  const runsQuery = useQuery({
    queryKey: runQueryKey(project.id, session?.session_token),
    queryFn: () =>
      apiClient.listProjectRuns(project.id, requireSessionToken(session), new Date().toISOString()),
    enabled: session !== null && activeStoryId !== "",
  });
  const snapshotsQuery = useQuery({
    queryKey: snapshotQueryKey(project.id, activeStoryId, session?.session_token),
    queryFn: () =>
      apiClient.listStorySnapshots(
        project.id,
        activeStoryId,
        requireSessionToken(session),
        new Date().toISOString(),
        "canon",
      ),
    enabled: session !== null && activeStoryId !== "",
  });
  const inspectImport = useMutation({
    mutationFn: (payload: ImportInspectRequest) =>
      apiClient.inspectImport(payload, requireSessionToken(session), new Date().toISOString()),
    onSuccess(result) {
      setInspectionResult(result);
    },
    onError() {
      setInspectionResult(null);
    },
  });
  const submitRun = useMutation({
    mutationFn: (importRecord: ImportRecord) => {
      const now = new Date().toISOString();
      const runId = createRunId(importRecord.import_id, now);
      return apiClient.submitImportRun(
        project.id,
        importRecord.story_id,
        importRecord.import_id,
        { run_id: runId, job_id: createJobId(runId), now },
        requireSessionToken(session),
        now,
      );
    },
    onSuccess(run) {
      queryClient.setQueryData(runQueryKey(project.id, session?.session_token), {
        runs: [
          run,
          ...(runsQuery.data?.runs ?? []).filter((candidate) => candidate.run_id !== run.run_id),
        ],
      });
      if (canDrainWorkerFromBrowser()) {
        drainLocalWorker.mutate();
        return;
      }
      void refreshProcessingState(queryClient, project.id, activeStoryId, session?.session_token);
    },
  });
  const drainLocalWorker = useMutation({
    mutationFn: () => {
      const now = new Date().toISOString();
      return apiClient.processWorkerJobs({ started_at: now, finished_at: now, max_jobs: 10 });
    },
    onSuccess() {
      void queryClient.invalidateQueries({
        queryKey: runQueryKey(project.id, session?.session_token),
      });
      void queryClient.invalidateQueries({
        queryKey: snapshotQueryKey(project.id, activeStoryId, session?.session_token),
      });
      void queryClient.invalidateQueries({ queryKey: ["project-status", project.id] });
      void queryClient.invalidateQueries({ queryKey: ["project-outputs", project.id] });
    },
  });
  const createImport = useMutation({
    mutationFn: ({ payload, storyId }: { payload: ImportInspectRequest; storyId: string }) => {
      const now = new Date().toISOString();
      return apiClient.createStoryImport(
        project.id,
        storyId,
        { ...payload, import_id: importId.trim(), now },
        requireSessionToken(session),
        now,
      );
    },
    onSuccess(importRecord) {
      queryClient.setQueryData(
        importQueryKey(project.id, importRecord.story_id, session?.session_token),
        {
          imports: [
            importRecord,
            ...(importsQuery.data?.imports ?? []).filter(
              (candidate) => candidate.import_id !== importRecord.import_id,
            ),
          ],
        },
      );
    },
  });
  const createDefaultStory = useMutation({
    mutationFn: () => {
      const now = new Date().toISOString();
      const title = defaultStoryTitle(project.name);
      return apiClient.createStory(
        project.id,
        { story_id: createStoryId(title), title, now },
        requireSessionToken(session),
        now,
      );
    },
    onSuccess(story) {
      setSelectedStoryId(story.story_id);
      saveActiveStoryId(project.id, story.story_id);
      setFormError(null);
      updateStoriesCache(
        queryClient,
        project.id,
        session?.session_token,
        story,
        storiesQuery.data?.stories ?? [],
      );
    },
  });

  const canSubmit = canBuildImportInspectPayload({
    sourceId,
    filename,
    title,
    sourceText,
    contentBase64: fileContentBase64,
  });
  const isInspectingImport = isReadingSourceFile || inspectImport.isPending;
  const isSourceTextOversized = sourceText.length > MAX_IMPORT_SOURCE_CHARACTERS;
  const sourceFileAccept = sourceFormats.data
    ? sourceFormatAcceptValue(sourceFormats.data.supported)
    : undefined;
  const sourceCountLabel = sourceFileStatusLabel({
    isReading: isReadingSourceFile,
    fileContentBase64,
    selectedFileName,
    selectedFileSize,
    sourceText,
  });
  const snapshotsByRun = new Map(
    (snapshotsQuery.data?.snapshots ?? []).map((snapshot) => [snapshot.run_id, snapshot]),
  );
  const latestRunByImportId = new Map<string, EngineRun>();
  for (const run of (runsQuery.data?.runs ?? []).filter((run) => run.story_id === activeStoryId)) {
    const existingRun = latestRunByImportId.get(run.import_id);
    if (!existingRun || runSortTimestamp(run) > runSortTimestamp(existingRun)) {
      latestRunByImportId.set(run.import_id, run);
    }
  }
  const projectRunsForActiveStory = [
    ...(runsQuery.data?.runs ?? []).filter((run) => run.story_id === activeStoryId),
  ].sort((left, right) => runSortTimestamp(right).localeCompare(runSortTimestamp(left)));

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    inspectImport.reset();
    createImport.reset();
    submitRun.reset();
    drainLocalWorker.reset();
    try {
      const deferredFormatError = deferredFormatMessage(filename, sourceFormats.data);
      if (deferredFormatError) {
        throw new Error(deferredFormatError);
      }
      const payload = buildImportInspectPayload({
        sourceId,
        filename,
        title,
        sourceText,
        contentBase64: fileContentBase64,
      });
      setFormError(null);
      setInspectionResult(null);
      inspectImport.mutate(payload);
    } catch (error) {
      setInspectionResult(null);
      setFormError(error instanceof Error ? error.message : "Import form is invalid.");
    }
  }

  async function saveImportMetadata() {
    createImport.reset();
    if (!importId.trim()) {
      setFormError("Import reference is required.");
      return;
    }
    try {
      const deferredFormatError = deferredFormatMessage(filename, sourceFormats.data);
      if (deferredFormatError) {
        throw new Error(deferredFormatError);
      }
      const payload = buildImportInspectPayload({
        sourceId,
        filename,
        title,
        sourceText,
        contentBase64: fileContentBase64,
      });
      setFormError(null);
      const storyId = activeStoryId || (await createDefaultStory.mutateAsync()).story_id;
      if (!confirmAdditionalStoryImport({ storyId })) {
        return;
      }
      createImport.mutate({ payload, storyId });
    } catch (error) {
      setFormError(error instanceof Error ? error.message : "Import form is invalid.");
    }
  }

  function confirmAdditionalStoryImport({ storyId }: { storyId: string }): boolean {
    const existingImports = storyId === activeStoryId ? (importsQuery.data?.imports ?? []) : [];
    if (existingImports.length === 0) {
      return true;
    }
    const storyTitle =
      storyOptions.find((story) => story.story_id === storyId)?.title ?? "this story";
    return window.confirm(
      `${storyTitle} already has imported source. Only continue if this source belongs to the same story. Add it anyway?`,
    );
  }

  function submitImportProcessing(importRecord: ImportRecord) {
    const existingRun = latestRunByImportId.get(importRecord.import_id);
    if (existingRun && existingRun.status !== "failed" && !isStaleActiveRun(existingRun)) {
      return;
    }
    submitRun.reset();
    drainLocalWorker.reset();
    submitRun.mutate(importRecord);
  }

  async function selectSourceFiles(fileList: FileList | null) {
    const files = Array.from(fileList ?? []);
    if (files.length === 0) {
      clearSelectedFile();
      return;
    }
    resetImportWorkflowState();
    setFileContentBase64("");
    setFormError(null);
    setIsReadingSourceFile(true);
    try {
      if (files.length === 1) {
        const [file] = files;
        setFilename(file.name);
        const generatedSourceId = sourceIdFromFilename(file.name);
        if (generatedSourceId) {
          setSourceId(generatedSourceId);
          setImportId(createImportId(generatedSourceId));
        }
        setSelectedFileName(file.name);
        setSelectedFileSize(file.size);
        setSourceText("");
        const bytes = await readFileBytes(file);
        setFileContentBase64(encodeBytesBase64(bytes));
      } else {
        const bundle = await readBundledSourceFiles(files);
        setFilename(bundle.filename);
        setSourceId(bundle.sourceId);
        setImportId(createImportId(bundle.sourceId));
        setTitle(title.trim() || "Chapter import");
        setSelectedFileName(`${files.length} files`);
        setSelectedFileSize(bundle.byteCount);
        setSourceText("");
        setFileContentBase64(encodeUtf8Base64(bundle.text));
      }
    } catch {
      setFileContentBase64("");
      setSelectedFileName("");
      setSelectedFileSize(0);
      setFormError(
        "Aevryn could not read that selection. Choose one native file, or multiple TXT, Markdown, HTML, or FB2 files.",
      );
    } finally {
      setIsReadingSourceFile(false);
    }
  }

  function clearSelectedFile() {
    setFileContentBase64("");
    setSelectedFileName("");
    setSelectedFileSize(0);
  }

  function resetImportWorkflowState() {
    inspectImport.reset();
    createImport.reset();
    submitRun.reset();
    drainLocalWorker.reset();
    setInspectionResult(null);
  }

  return (
    <div className="workspace-view-stack">
      <div>
        <p className="eyebrow">Import</p>
        <h2>Import</h2>
      </div>

      <StatusPanel title="Native Source Formats">
        {sourceFormats.isLoading ? <LoadingMessage>Loading source formats.</LoadingMessage> : null}
        {sourceFormats.error ? <ErrorMessage>{sourceFormats.error.message}</ErrorMessage> : null}
        {sourceFormats.data ? (
          <div className="format-grid">
            <FormatColumn
              title="Supported"
              items={sourceFormats.data.supported.map((item) => item.extension)}
            />
            <FormatColumn
              title="Deferred"
              items={sourceFormats.data.deferred.map((item) => item.extension)}
            />
          </div>
        ) : null}
      </StatusPanel>

      <section className="project-panel">
        <h2>Source Intake</h2>
        <form className="import-form" onSubmit={submit}>
          {(storiesQuery.data?.stories.length ?? 0) > 0 ? (
            <label>
              Story
              <select
                value={activeStoryId}
                onChange={(event) => {
                  const storyId = event.target.value;
                  setSelectedStoryId(storyId);
                  saveActiveStoryId(project.id, storyId);
                }}
                disabled={storiesQuery.isLoading}
              >
                {(storiesQuery.data?.stories ?? []).map((story) => (
                  <option key={story.story_id} value={story.story_id}>
                    {story.title}
                  </option>
                ))}
              </select>
            </label>
          ) : (
            <p className="field-note">
              Aevryn will create a story record when you save this import.
            </p>
          )}
          <div className="form-row-grid">
            <label>
              Filename
              <input value={filename} onChange={(event) => setFilename(event.target.value)} />
            </label>
            <label>
              Title
              <input value={title} onChange={(event) => setTitle(event.target.value)} />
            </label>
          </div>
          <details className="advanced-fields">
            <summary>Advanced import references</summary>
            <div className="form-row-grid">
              <label>
                Import reference
                <input value={importId} onChange={(event) => setImportId(event.target.value)} />
              </label>
              <label>
                Source reference
                <input value={sourceId} onChange={(event) => setSourceId(event.target.value)} />
              </label>
            </div>
          </details>
          <label>
            Source file
            <input
              type="file"
              multiple
              accept={sourceFileAccept}
              onChange={(event) => {
                void selectSourceFiles(event.target.files);
              }}
            />
          </label>
          {fileContentBase64 ? (
            <button type="button" className="secondary-button" onClick={clearSelectedFile}>
              Clear selected file
            </button>
          ) : null}
          <label>
            Source text
            <textarea
              value={sourceText}
              onChange={(event) => setSourceText(event.target.value)}
              rows={10}
              aria-describedby="source-text-count"
              disabled={Boolean(fileContentBase64)}
            />
          </label>
          <p
            id="source-text-count"
            className={isSourceTextOversized ? "field-note field-note-error" : "field-note"}
          >
            {sourceCountLabel}
          </p>
          {formError ? <ErrorMessage>{formError}</ErrorMessage> : null}
          {inspectImport.error ? <ErrorMessage>{inspectImport.error.message}</ErrorMessage> : null}
          {createImport.error ? <ErrorMessage>{createImport.error.message}</ErrorMessage> : null}
          {createDefaultStory.error ? (
            <ErrorMessage>{createDefaultStory.error.message}</ErrorMessage>
          ) : null}
          {submitRun.error ? <ErrorMessage>{submitRun.error.message}</ErrorMessage> : null}
          {canDrainWorkerFromBrowser() && drainLocalWorker.error ? (
            <ErrorMessage>{drainLocalWorker.error.message}</ErrorMessage>
          ) : null}
          <button
            type="submit"
            className="primary-button"
            aria-busy={isInspectingImport}
            disabled={!canSubmit || isInspectingImport}
          >
            {importInspectButtonLabel({
              isReading: isReadingSourceFile,
              isInspecting: inspectImport.isPending,
            })}
          </button>
        </form>
      </section>

      <section className="project-panel" aria-label="Web import">
        <h2>Web Import</h2>
        <div className="import-form">
          <label>
            Source URL
            <input value="" placeholder="https://example.com/story" disabled readOnly />
          </label>
          <p className="field-note">
            Unavailable: permission checks are required before web intake.
          </p>
          <button type="button" className="secondary-button" disabled>
            Check permissions
          </button>
        </div>
      </section>

      {inspectionResult ? (
        <section className="project-panel" aria-label="Import inspection result">
          <h2>Import Structure</h2>
          <p className="result-summary">{importResultTotalsLabel(inspectionResult)}</p>
          <dl className="metric-grid">
            <div>
              <dt>Format</dt>
              <dd>{inspectionResult.source_format}</dd>
            </div>
            <div>
              <dt>Chapters</dt>
              <dd>{inspectionResult.chapters}</dd>
            </div>
            <div>
              <dt>Scenes</dt>
              <dd>{inspectionResult.scenes}</dd>
            </div>
            <div>
              <dt>Paragraphs</dt>
              <dd>{inspectionResult.paragraphs}</dd>
            </div>
            <div>
              <dt>Evidence anchors</dt>
              <dd>{inspectionResult.evidence_anchors}</dd>
            </div>
            <div>
              <dt>Input</dt>
              <dd>{fileContentBase64 ? "Uploaded file" : "Pasted text"}</dd>
            </div>
          </dl>
          {inspectionResult.scene_map.length > 0 ? (
            <div className="compact-list" aria-label="Scene map">
              {importScenePreviewRows(inspectionResult).map((scene) => (
                <div key={scene.scene_id} className="compact-row">
                  <strong>{scene.title}</strong>
                  <span>Chapter {scene.chapter_index}</span>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState title="No scenes found">
              The import returned no scene map entries.
            </EmptyState>
          )}
          <button
            type="button"
            className="secondary-button"
            disabled={createImport.isPending || createDefaultStory.isPending}
            onClick={() => {
              void saveImportMetadata();
            }}
          >
            {createImport.isPending || createDefaultStory.isPending
              ? "Saving import"
              : "Save import"}
          </button>
        </section>
      ) : null}

      {activeStoryId ? (
        <section className="project-panel" aria-label="Saved imports">
          <h2>Saved Imports</h2>
          {importsQuery.isLoading ? <LoadingMessage>Loading saved imports.</LoadingMessage> : null}
          {importsQuery.error ? <ErrorMessage>{importsQuery.error.message}</ErrorMessage> : null}
          {!importsQuery.isLoading &&
          !importsQuery.error &&
          (importsQuery.data?.imports.length ?? 0) === 0 ? (
            <EmptyState title="No saved imports">
              Save import metadata after inspecting source.
            </EmptyState>
          ) : null}
          {(importsQuery.data?.imports ?? []).length > 0 ? (
            <div className="compact-list">
              {(importsQuery.data?.imports ?? []).map((importRecord, index) => {
                const run = latestRunByImportId.get(importRecord.import_id);
                const processingAction = importProcessingAction(run, submitRun.isPending);
                return (
                  <div key={importRecord.import_id} className="compact-row">
                    <strong>{importCardTitle(index)}</strong>
                    <span>{sceneCountLabel(importRecord.scene_count)}</span>
                    <button
                      type="button"
                      className="secondary-button"
                      disabled={processingAction.disabled}
                      onClick={() => submitImportProcessing(importRecord)}
                    >
                      {processingAction.label}
                    </button>
                  </div>
                );
              })}
            </div>
          ) : null}
        </section>
      ) : null}

      <section className="project-panel" aria-label="Project runs">
        <h2>Project Runs</h2>
        <NavLink className="secondary-button" to={`/projects/${project.id}/monitoring`}>
          View monitoring
        </NavLink>
        {runsQuery.isLoading ? <LoadingMessage>Loading project runs.</LoadingMessage> : null}
        {runsQuery.error && !runsQuery.data ? (
          <ErrorMessage>{runsQuery.error.message}</ErrorMessage>
        ) : null}
        {snapshotsQuery.error ? <ErrorMessage>{snapshotsQuery.error.message}</ErrorMessage> : null}
        {!runsQuery.isLoading && !runsQuery.error && (runsQuery.data?.runs.length ?? 0) === 0 ? (
          <EmptyState title="No project runs">
            Submit a saved import for background processing.
          </EmptyState>
        ) : null}
        {projectRunsForActiveStory.length > 0 ? (
          <div className="compact-list">
            {projectRunsForActiveStory.map((run) => {
              const errorLabel = runErrorLabel(run);
              return (
                <div key={run.run_id} className="compact-row">
                  <strong>Processing run</strong>
                  <span>{formatRunStatus(run.status)} run</span>
                  <span>{runSnapshotLabel(run, snapshotsByRun.get(run.run_id))}</span>
                  {isActiveRun(run) ? (
                    <span>Results will appear when the canon snapshot is ready.</span>
                  ) : null}
                  {errorLabel ? <span>{errorLabel}</span> : null}
                </div>
              );
            })}
          </div>
        ) : null}
      </section>
    </div>
  );
}

function updateStoriesCache(
  queryClient: QueryClient,
  projectId: string,
  sessionToken: string | undefined,
  story: Story,
  existingStories: Story[],
) {
  queryClient.setQueryData(storyQueryKey(projectId, sessionToken), {
    stories: [
      story,
      ...existingStories.filter((candidate) => candidate.story_id !== story.story_id),
    ],
  });
}

async function readFileBytes(file: File): Promise<Uint8Array> {
  if (typeof file.arrayBuffer === "function") {
    try {
      return new Uint8Array(await file.arrayBuffer());
    } catch {
      // Fall through to alternate browser/jsdom readers.
    }
  }
  if (typeof file.text === "function") {
    try {
      return new TextEncoder().encode(await file.text());
    } catch {
      // Fall through to FileReader.
    }
  }
  return readFileBytesWithFileReader(file);
}

function readFileBytesWithFileReader(file: File): Promise<Uint8Array> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error("File could not be read."));
    reader.onload = () => {
      if (reader.result instanceof ArrayBuffer) {
        resolve(new Uint8Array(reader.result));
        return;
      }
      reject(new Error("File reader returned an unexpected result."));
    };
    reader.readAsArrayBuffer(file);
  });
}

type BundledSourceFiles = {
  filename: string;
  sourceId: string;
  text: string;
  byteCount: number;
};

async function readBundledSourceFiles(files: File[]): Promise<BundledSourceFiles> {
  if (files.some((file) => !canBundleSourceFile(file.name))) {
    throw new Error("Only text-like files can be bundled.");
  }
  const chapters = await Promise.all(
    files.map(async (file) => {
      const text = await readFileText(file);
      return `File: ${file.name}\n\n${text.trimEnd()}`;
    }),
  );
  return {
    filename: "aevryn_import_bundle.txt",
    sourceId: "aevryn_import_bundle",
    text: chapters.join("\n\n---\n\n"),
    byteCount: files.reduce((total, file) => total + file.size, 0),
  };
}

async function readFileText(file: File): Promise<string> {
  if (typeof file.text === "function") {
    return file.text();
  }
  return new TextDecoder().decode(await readFileBytes(file));
}

function canBundleSourceFile(filename: string): boolean {
  const normalized = filename.trim().toLowerCase();
  return [".txt", ".md", ".markdown", ".html", ".htm", ".xhtml", ".fb2"].some((extension) =>
    normalized.endsWith(extension),
  );
}

function sourceFileStatusLabel({
  isReading,
  fileContentBase64,
  selectedFileName,
  selectedFileSize,
  sourceText,
}: {
  isReading: boolean;
  fileContentBase64: string;
  selectedFileName: string;
  selectedFileSize: number;
  sourceText: string;
}): string {
  if (isReading) {
    return "Reading selected file.";
  }
  if (fileContentBase64) {
    return `${selectedFileName} / ${selectedFileSize.toLocaleString()} bytes selected`;
  }
  return importSourceCharacterCountLabel(sourceText);
}

function importInspectButtonLabel({
  isReading,
  isInspecting,
}: {
  isReading: boolean;
  isInspecting: boolean;
}): string {
  if (isReading) {
    return "Reading file";
  }
  return isInspecting ? "Inspecting" : "Inspect import";
}

function deferredFormatMessage(filename: string, formats: SourceFormats | undefined): string {
  const normalizedFilename = filename.trim().toLowerCase();
  const match = formats?.deferred.find((format) =>
    sourceFormatExtensions(format.extension).some((extension) =>
      normalizedFilename.endsWith(extension.toLowerCase()),
    ),
  );
  if (!match) {
    return "";
  }
  return `${match.extension} import is deferred. ${match.notes}`;
}

function sourceFormatAcceptValue(formats: SourceFormats["supported"]): string {
  return formats
    .flatMap((format) => sourceFormatExtensions(format.extension))
    .filter((extension, index, extensions) => extensions.indexOf(extension) === index)
    .join(",");
}

function sourceFormatExtensions(value: string): string[] {
  return value
    .split("/")
    .map((extension) => extension.trim())
    .filter((extension) => extension.startsWith("."));
}

function importQueryKey(projectId: string, storyId: string, sessionToken: string | undefined) {
  return ["story-imports", projectId, storyId, sessionToken] as const;
}

function runQueryKey(projectId: string, sessionToken: string | undefined) {
  return ["project-runs", projectId, sessionToken] as const;
}

function snapshotQueryKey(projectId: string, storyId: string, sessionToken: string | undefined) {
  return ["story-snapshots", projectId, storyId, "canon", sessionToken] as const;
}

function storyQueryKey(projectId: string, sessionToken: string | undefined) {
  return ["project-stories", projectId, sessionToken] as const;
}

function defaultStoryTitle(projectName: string): string {
  return `${projectName} Story`;
}

function createStoryId(title: string): string {
  const slug = title
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, 80);
  return `story_${slug || "untitled"}`;
}

function createImportId(sourceId: string): string {
  return `import_${machineSuffix(sourceId)}_${machineSuffix(new Date().toISOString())}`;
}

function runSnapshotLabel(run: EngineRun, snapshot: Snapshot | undefined): string {
  if (run.status === "failed") {
    return "No snapshot: run failed";
  }
  if (snapshot) {
    return "Canon snapshot ready";
  }
  if (run.status === "succeeded") {
    return "Snapshot pending";
  }
  return "Snapshot waiting";
}

function importCardTitle(index: number): string {
  return index === 0 ? "Chapter import" : `Chapter import ${index + 1}`;
}

function sceneCountLabel(count: number): string {
  return count === 1 ? "1 scene" : `${count.toLocaleString()} scenes`;
}

function importProcessingAction(
  run: EngineRun | undefined,
  isSubmitting: boolean,
): { label: string; disabled: boolean } {
  if (isSubmitting) {
    return { label: "Submitting", disabled: true };
  }
  if (!run) {
    return { label: "Submit processing", disabled: false };
  }
  if (isStaleActiveRun(run)) {
    return { label: "Retry processing", disabled: false };
  }
  if (run.status === "failed") {
    return { label: "Retry processing", disabled: false };
  }
  if (run.status === "succeeded") {
    return { label: "Processed", disabled: true };
  }
  return { label: "Processing", disabled: true };
}

function canDrainWorkerFromBrowser(): boolean {
  const configured = import.meta.env.VITE_AEVRYN_BROWSER_WORKER_DRAIN_ENABLED;
  if (configured === "true") {
    return true;
  }
  if (configured === "false") {
    return false;
  }
  if (typeof window === "undefined") {
    return false;
  }
  return ["localhost", "127.0.0.1", "::1"].includes(window.location.hostname);
}

async function refreshProcessingState(
  queryClient: QueryClient,
  projectId: string,
  storyId: string,
  sessionToken: string | undefined,
): Promise<void> {
  await Promise.all([
    queryClient.invalidateQueries({
      queryKey: runQueryKey(projectId, sessionToken),
    }),
    queryClient.invalidateQueries({
      queryKey: snapshotQueryKey(projectId, storyId, sessionToken),
    }),
    queryClient.invalidateQueries({ queryKey: ["project-status", projectId] }),
    queryClient.invalidateQueries({ queryKey: ["project-outputs", projectId] }),
  ]);
}

function isActiveRun(run: EngineRun): boolean {
  return run.status !== "failed" && run.status !== "succeeded" && !isStaleActiveRun(run);
}

function runSortTimestamp(run: EngineRun): string {
  return run.status_updated_at ?? run.finished_at ?? run.started_at;
}

function runErrorLabel(run: EngineRun): string {
  if (run.error_summary) {
    return `Run error: ${runErrorSummary(run.error_summary)}`;
  }
  if (isStaleActiveRun(run)) {
    return "Run error: Processing timed out before completion.";
  }
  if (run.status === "failed") {
    return "Run error: No error summary provided.";
  }
  return "";
}

function runErrorSummary(summary: string): string {
  if (summary.startsWith("Unknown evidence anchor:")) {
    return (
      "Import evidence could not be matched during AI extraction. " +
      "Review the import structure, then retry processing. If it repeats, " +
      "split the import into smaller chapter batches."
    );
  }
  if (summary.startsWith("Conflicting fact:")) {
    return (
      "AI extraction produced conflicting canon facts. Retry processing. " +
      "If it repeats, review the import structure or split the import into " +
      "smaller chapter batches."
    );
  }
  if (summary === "World sheet section titles must be unique.") {
    return (
      "World sheet output contained duplicate sections. Aevryn merged matching " +
      "sections; retry processing."
    );
  }
  if (summary === "OpenAI extraction request timed out.") {
    return (
      "AI extraction timed out while reading the provider response. Retry with " +
      "a smaller chapter batch or increase the provider timeout for large imports."
    );
  }
  return summary;
}

function isStaleActiveRun(run: EngineRun): boolean {
  if (run.status !== "pending" && run.status !== "running") {
    return false;
  }
  const updatedAt = Date.parse(run.status_updated_at ?? run.started_at);
  if (!Number.isFinite(updatedAt)) {
    return false;
  }
  return Date.now() - updatedAt > 30 * 60 * 1000;
}

function createRunId(importId: string, now: string): string {
  return `${importId}_run_${machineSuffix(now)}`;
}

function createJobId(runId: string): string {
  return `${runId}_job`;
}

function machineSuffix(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
}

function requireSessionToken(session: { session_token: string } | null): string {
  if (!session) {
    throw new Error("Aevryn session is required.");
  }
  return session.session_token;
}

function FormatColumn({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="format-column">
      <h3>{title}</h3>
      {items.length > 0 ? (
        <ul>
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : (
        <p>None reported.</p>
      )}
    </div>
  );
}
