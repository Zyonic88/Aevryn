import { useMutation, useQuery, useQueryClient, type QueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";

import { apiClient, type ImportInspectRequest } from "../api/client";
import { useAuth } from "../auth/useAuth";
import { EmptyState, ErrorMessage, LoadingMessage, StatusPanel } from "../components/Feedback";
import {
  MAX_IMPORT_SOURCE_CHARACTERS,
  buildImportInspectPayload,
  canBuildImportInspectPayload,
  encodeBytesBase64,
  importSourceCharacterCountLabel,
  sourceIdFromFilename,
} from "../importing/importPayload";
import { formatRunStatus } from "../formatting/display";
import {
  importResultTotalsLabel,
  importScenePreviewRows,
  importScenePreviewSummary,
} from "../importing/importResult";
import type { EngineRun, ImportInspect, ImportRecord, Snapshot, Story } from "../api/schemas";
import type { SourceFormats } from "../api/schemas";
import type { ProjectSummary } from "../projects/projectStore";

const DEFAULT_IMPORT_TEXT = "Chapter 1\n";

export function ImportWorkspaceView({ project }: { project: ProjectSummary }) {
  const { session } = useAuth();
  const queryClient = useQueryClient();
  const [selectedStoryId, setSelectedStoryId] = useState("");
  const [importId, setImportId] = useState(project.id.replace(/^project_/, "import_"));
  const [sourceId, setSourceId] = useState(project.id.replace(/^project_/, "source_"));
  const [filename, setFilename] = useState("chapter_001.txt");
  const [title, setTitle] = useState(project.name);
  const [sourceText, setSourceText] = useState(DEFAULT_IMPORT_TEXT);
  const [fileContentBase64, setFileContentBase64] = useState("");
  const [selectedFileName, setSelectedFileName] = useState("");
  const [selectedFileSize, setSelectedFileSize] = useState(0);
  const [formError, setFormError] = useState<string | null>(null);
  const [inspectionResult, setInspectionResult] = useState<ImportInspect | null>(null);
  const [savedImport, setSavedImport] = useState<ImportRecord | null>(null);
  const [submittedRun, setSubmittedRun] = useState<EngineRun | null>(null);

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
  const activeStoryId = selectedStoryId || storiesQuery.data?.stories[0]?.story_id || "";
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
    mutationFn: (payload: ImportInspectRequest) => apiClient.inspectImport(payload),
    onSuccess(result) {
      setInspectionResult(result);
      setSavedImport(null);
    },
    onError() {
      setInspectionResult(null);
      setSavedImport(null);
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
      setSubmittedRun(run);
      queryClient.setQueryData(runQueryKey(project.id, session?.session_token), {
        runs: [
          run,
          ...(runsQuery.data?.runs ?? []).filter((candidate) => candidate.run_id !== run.run_id),
        ],
      });
    },
  });
  const createImport = useMutation({
    mutationFn: ({
      payload,
      storyId,
    }: {
      payload: ImportInspectRequest;
      storyId: string;
    }) => {
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
      setSavedImport(importRecord);
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
  const isSourceTextOversized = sourceText.length > MAX_IMPORT_SOURCE_CHARACTERS;
  const sourceFileAccept = sourceFormats.data
    ? sourceFormatAcceptValue(sourceFormats.data.supported)
    : undefined;
  const sourceCountLabel = fileContentBase64
    ? `${selectedFileName} / ${selectedFileSize.toLocaleString()} bytes selected`
    : importSourceCharacterCountLabel(sourceText);
  const snapshotsByRun = new Map(
    (snapshotsQuery.data?.snapshots ?? []).map((snapshot) => [snapshot.run_id, snapshot]),
  );

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    inspectImport.reset();
    createImport.reset();
    submitRun.reset();
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
      setSavedImport(null);
      setSubmittedRun(null);
      inspectImport.mutate(payload);
    } catch (error) {
      setInspectionResult(null);
      setSavedImport(null);
      setSubmittedRun(null);
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
      createImport.mutate({ payload, storyId });
    } catch (error) {
      setFormError(error instanceof Error ? error.message : "Import form is invalid.");
    }
  }

  function submitImportProcessing(importRecord: ImportRecord) {
    submitRun.reset();
    setSubmittedRun(null);
    submitRun.mutate(importRecord);
  }

  async function selectSourceFile(file: File | null) {
    if (!file) {
      clearSelectedFile();
      return;
    }
    setFilename(file.name);
    const generatedSourceId = sourceIdFromFilename(file.name);
    if (generatedSourceId) {
      setSourceId(generatedSourceId);
    }
    setSelectedFileName(file.name);
    setSelectedFileSize(file.size);
    setFormError(null);
    try {
      const bytes = await readFileBytes(file);
      setFileContentBase64(encodeBytesBase64(bytes));
    } catch {
      setFileContentBase64("");
      setSelectedFileName("");
      setSelectedFileSize(0);
      setFormError("Aevryn could not read that file. Try a supported TXT, Markdown, HTML, FB2, DOCX, ODT, or EPUB file.");
    }
  }

  function clearSelectedFile() {
    setFileContentBase64("");
    setSelectedFileName("");
    setSelectedFileSize(0);
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
                onChange={(event) => setSelectedStoryId(event.target.value)}
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
            <p className="field-note">Aevryn will create a story record when you save this import.</p>
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
              accept={sourceFileAccept}
              onChange={(event) => {
                void selectSourceFile(event.target.files?.[0] ?? null);
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
          <button
            type="submit"
            className="primary-button"
            disabled={!canSubmit || inspectImport.isPending}
          >
            {inspectImport.isPending ? "Inspecting" : "Inspect import"}
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
          <p className="field-note">Unavailable: permission checks are required before web intake.</p>
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
              <dt>Source</dt>
              <dd>{filename}</dd>
            </div>
          </dl>
          {inspectionResult.scene_map.length > 0 ? (
            <>
              <p className="field-note">{importScenePreviewSummary(inspectionResult)}</p>
              <div className="compact-list" aria-label="Scene map">
                {importScenePreviewRows(inspectionResult).map((scene) => (
                  <div key={scene.scene_id} className="compact-row">
                    <strong>{scene.title}</strong>
                    <span>Chapter {scene.chapter_index}</span>
                  </div>
                ))}
              </div>
            </>
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
          {savedImport ? (
            <p className="field-note">Saved {savedImport.filename} for this story.</p>
          ) : null}
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
              {(importsQuery.data?.imports ?? []).map((importRecord) => (
                <div key={importRecord.import_id} className="compact-row">
                  <strong>{importRecord.filename}</strong>
                  <span>{importRecord.scene_count} scenes</span>
                  <button
                    type="button"
                    className="secondary-button"
                    disabled={submitRun.isPending}
                    onClick={() => submitImportProcessing(importRecord)}
                  >
                    {submitRun.isPending ? "Submitting" : "Submit processing"}
                  </button>
                </div>
              ))}
            </div>
          ) : null}
          {submittedRun ? (
            <p className="field-note">Submitted {savedImport?.filename ?? "import"} for processing.</p>
          ) : null}
        </section>
      ) : null}

      <section className="project-panel" aria-label="Project runs">
        <h2>Project Runs</h2>
        {runsQuery.isLoading ? <LoadingMessage>Loading project runs.</LoadingMessage> : null}
        {runsQuery.error && !runsQuery.data ? <ErrorMessage>{runsQuery.error.message}</ErrorMessage> : null}
        {snapshotsQuery.error ? <ErrorMessage>{snapshotsQuery.error.message}</ErrorMessage> : null}
        {!runsQuery.isLoading && !runsQuery.error && (runsQuery.data?.runs.length ?? 0) === 0 ? (
          <EmptyState title="No project runs">
            Submit a saved import for background processing.
          </EmptyState>
        ) : null}
        {(runsQuery.data?.runs ?? []).length > 0 ? (
          <div className="compact-list">
            {(runsQuery.data?.runs ?? []).map((run) => {
              const errorLabel = runErrorLabel(run);
              return (
                <div key={run.run_id} className="compact-row">
                  <strong>Processing run</strong>
                  <span>{formatRunStatus(run.status)} run</span>
                  <span>{runSnapshotLabel(run, snapshotsByRun.get(run.run_id))}</span>
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

function snapshotQueryKey(
  projectId: string,
  storyId: string,
  sessionToken: string | undefined,
) {
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

function runErrorLabel(run: EngineRun): string {
  if (run.error_summary) {
    return `Run error: ${run.error_summary}`;
  }
  if (run.status === "failed") {
    return "Run error: No error summary provided.";
  }
  return "";
}

function createRunId(importId: string, now: string): string {
  return `${importId}_run_${machineSuffix(now)}`;
}

function createJobId(runId: string): string {
  return `${runId}_job`;
}

function machineSuffix(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "");
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
