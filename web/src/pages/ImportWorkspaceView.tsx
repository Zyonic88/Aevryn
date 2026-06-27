import { useMutation, useQuery } from "@tanstack/react-query";
import { FormEvent, useState } from "react";

import { apiClient, type ImportInspectRequest } from "../api/client";
import { EmptyState, ErrorMessage, LoadingMessage, StatusPanel } from "../components/Feedback";
import {
  MAX_IMPORT_SOURCE_CHARACTERS,
  buildImportInspectPayload,
  canBuildImportInspectPayload,
  importSourceCharacterCountLabel,
} from "../importing/importPayload";
import {
  importResultTotalsLabel,
  importScenePreviewRows,
  importScenePreviewSummary,
} from "../importing/importResult";
import type { ImportInspect } from "../api/schemas";
import type { ProjectSummary } from "../projects/projectStore";

const DEFAULT_IMPORT_TEXT = "Chapter 1\n";

export function ImportWorkspaceView({ project }: { project: ProjectSummary }) {
  const [sourceId, setSourceId] = useState(project.id.replace(/^project_/, "source_"));
  const [filename, setFilename] = useState("chapter_001.txt");
  const [title, setTitle] = useState(project.name);
  const [sourceText, setSourceText] = useState(DEFAULT_IMPORT_TEXT);
  const [formError, setFormError] = useState<string | null>(null);
  const [inspectionResult, setInspectionResult] = useState<ImportInspect | null>(null);

  const sourceFormats = useQuery({
    queryKey: ["source-formats"],
    queryFn: () => apiClient.sourceFormats(),
  });
  const inspectImport = useMutation({
    mutationFn: (payload: ImportInspectRequest) => apiClient.inspectImport(payload),
    onSuccess(result) {
      setInspectionResult(result);
    },
    onError() {
      setInspectionResult(null);
    },
  });

  const canSubmit = canBuildImportInspectPayload({ sourceId, filename, title, sourceText });
  const isSourceTextOversized = sourceText.length > MAX_IMPORT_SOURCE_CHARACTERS;
  const sourceCountLabel = importSourceCharacterCountLabel(sourceText);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    inspectImport.reset();
    try {
      const payload = buildImportInspectPayload({ sourceId, filename, title, sourceText });
      setFormError(null);
      setInspectionResult(null);
      inspectImport.mutate(payload);
    } catch (error) {
      setInspectionResult(null);
      setFormError(error instanceof Error ? error.message : "Import form is invalid.");
    }
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
        <h2>Paste Source</h2>
        <form className="import-form" onSubmit={submit}>
          <div className="form-row-grid">
            <label>
              Source ID
              <input value={sourceId} onChange={(event) => setSourceId(event.target.value)} />
            </label>
            <label>
              Filename
              <input value={filename} onChange={(event) => setFilename(event.target.value)} />
            </label>
          </div>
          <label>
            Title
            <input value={title} onChange={(event) => setTitle(event.target.value)} />
          </label>
          <label>
            Source text
            <textarea
              value={sourceText}
              onChange={(event) => setSourceText(event.target.value)}
              rows={10}
              aria-describedby="source-text-count"
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
          <button
            type="submit"
            className="primary-button"
            disabled={!canSubmit || inspectImport.isPending}
          >
            {inspectImport.isPending ? "Inspecting" : "Inspect import"}
          </button>
        </form>
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
              <dd>{inspectionResult.source_id}</dd>
            </div>
          </dl>
          {inspectionResult.scene_map.length > 0 ? (
            <>
              <p className="field-note">{importScenePreviewSummary(inspectionResult)}</p>
              <div className="compact-list" aria-label="Scene map">
                {importScenePreviewRows(inspectionResult).map((scene) => (
                  <div key={scene.scene_id} className="compact-row">
                    <strong>{scene.title}</strong>
                    <span>{scene.scene_id}</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <EmptyState title="No scenes found">
              The import returned no scene map entries.
            </EmptyState>
          )}
        </section>
      ) : null}
    </div>
  );
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
