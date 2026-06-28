import { useMutation } from "@tanstack/react-query";
import { FormEvent, useState } from "react";

import { apiClient, type ExportPreviewRequest } from "../api/client";
import type { ExportPreview } from "../api/schemas";
import { ErrorMessage } from "../components/Feedback";
import {
  DeveloperPreviewToggle,
  ProjectOutputSummaryPanel,
} from "../output/ProjectOutputSummaryPanel";
import {
  buildExportPreviewPayload,
  canSubmitExportPreviewInput,
} from "../previewing/previewPayload";
import type { ProjectSummary } from "../projects/projectStore";

const DEFAULT_SOURCE_TEXT = "Chapter 1\n";
const DEFAULT_AI_RESPONSE =
  '{\n  "entities": [],\n  "facts": [],\n  "relationships": [],\n  "state_changes": []\n}';

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
  const [sourceId, setSourceId] = useState(project.id.replace(/^project_/, "source_"));
  const [filename, setFilename] = useState("chapter_001.txt");
  const [title, setTitle] = useState(project.name);
  const [sourceText, setSourceText] = useState(DEFAULT_SOURCE_TEXT);
  const [aiResponseText, setAiResponseText] = useState(DEFAULT_AI_RESPONSE);
  const [characterIdsText, setCharacterIdsText] = useState("");
  const [worldEntityIdsText, setWorldEntityIdsText] = useState("");
  const [sceneId, setSceneId] = useState("");
  const [selectedExport, setSelectedExport] = useState(optionValue(exportOptions[0]));
  const [formError, setFormError] = useState<string | null>(null);
  const [previewResult, setPreviewResult] = useState<ExportPreview | null>(null);

  const activeExport = parseOptionValue(selectedExport);
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

      <DeveloperPreviewToggle>
        <section>
          <h2>Export Preview</h2>
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
              rows={8}
            />
          </label>
          <label>
            AI response JSON
            <textarea
              value={aiResponseText}
              onChange={(event) => setAiResponseText(event.target.value)}
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

function ExportPreviewResult({ result }: { result: ExportPreview }) {
  return (
    <section className="project-panel" aria-label="Export preview result">
      <h2>{result.filename}</h2>
      <dl className="metric-grid export-metadata">
        <div>
          <dt>Kind</dt>
          <dd>{result.export_kind}</dd>
        </div>
        <div>
          <dt>Format</dt>
          <dd>{result.export_format}</dd>
        </div>
        <div>
          <dt>Content Type</dt>
          <dd>{result.content_type}</dd>
        </div>
      </dl>
      <pre className="export-preview-content">{result.content}</pre>
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
