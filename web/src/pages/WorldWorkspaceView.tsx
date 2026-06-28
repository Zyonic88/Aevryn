import { useMutation } from "@tanstack/react-query";
import { FormEvent, useState } from "react";

import { apiClient, type WorldPreviewRequest } from "../api/client";
import type { OutputSection, WorldPreview } from "../api/schemas";
import { EmptyState, ErrorMessage } from "../components/Feedback";
import {
  DeveloperPreviewToggle,
  ProjectOutputSummaryPanel,
} from "../output/ProjectOutputSummaryPanel";
import { readableOutputItems } from "../output/readableOutput";
import { buildWorldPreviewPayload, canSubmitWorldPreviewInput } from "../previewing/previewPayload";
import type { ProjectSummary } from "../projects/projectStore";

const DEFAULT_SOURCE_TEXT = "Chapter 1\n";
const DEFAULT_AI_RESPONSE =
  '{\n  "entities": [],\n  "facts": [],\n  "relationships": [],\n  "state_changes": []\n}';

export function WorldWorkspaceView({ project }: { project: ProjectSummary }) {
  const [sourceId, setSourceId] = useState(project.id.replace(/^project_/, "source_"));
  const [filename, setFilename] = useState("chapter_001.txt");
  const [title, setTitle] = useState(project.name);
  const [sourceText, setSourceText] = useState(DEFAULT_SOURCE_TEXT);
  const [aiResponseText, setAiResponseText] = useState(DEFAULT_AI_RESPONSE);
  const [worldEntityIdsText, setWorldEntityIdsText] = useState("");
  const [sceneId, setSceneId] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [previewResult, setPreviewResult] = useState<WorldPreview | null>(null);

  const previewWorld = useMutation({
    mutationFn: (payload: WorldPreviewRequest) => apiClient.previewWorld(payload),
    onSuccess(result) {
      setPreviewResult(result);
    },
    onError() {
      setPreviewResult(null);
    },
  });

  const canSubmit = canSubmitWorldPreviewInput({
    sourceId,
    filename,
    title,
    sourceText,
    aiResponseText,
    worldEntityIdsText,
    sceneId,
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    previewWorld.reset();
    try {
      const payload = buildWorldPreviewPayload({
        sourceId,
        filename,
        title,
        sourceText,
        aiResponseText,
        worldEntityIdsText,
        sceneId,
      });
      setFormError(null);
      setPreviewResult(null);
      previewWorld.mutate(payload);
    } catch (error) {
      setPreviewResult(null);
      setFormError(error instanceof Error ? error.message : "World preview form is invalid.");
    }
  }

  return (
    <div className="workspace-view-stack">
      <div>
        <p className="eyebrow">World</p>
        <h2>World</h2>
      </div>

      <ProjectOutputSummaryPanel project={project} surface="world" />

      <DeveloperPreviewToggle>
        <section>
          <h2>World Preview</h2>
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
              World entity IDs
              <input
                value={worldEntityIdsText}
                onChange={(event) => setWorldEntityIdsText(event.target.value)}
                placeholder="Optional: location_hangar building_fortress"
              />
            </label>
            <label>
              Scene ID
              <input
                value={sceneId}
                onChange={(event) => setSceneId(event.target.value)}
                placeholder="Optional scene ID"
              />
            </label>
          </div>
          {formError ? <ErrorMessage>{formError}</ErrorMessage> : null}
          {previewWorld.error ? <ErrorMessage>{previewWorld.error.message}</ErrorMessage> : null}
          <button
            type="submit"
            className="primary-button"
            disabled={!canSubmit || previewWorld.isPending}
          >
            {previewWorld.isPending ? "Building preview" : "Preview world"}
          </button>
          </form>
        </section>
      </DeveloperPreviewToggle>

      {previewResult ? <WorldPreviewResult result={previewResult} /> : null}
    </div>
  );
}

function WorldPreviewResult({ result }: { result: WorldPreview }) {
  const world = result.world_sheet;
  return (
    <section className="project-panel" aria-label="World preview result">
      <h2>World Sheet</h2>
      {world.entity_sections.length > 0 ? (
        <div className="profile-grid">
          {world.entity_sections.map((section) => (
            <WorldEntitySection key={section.title} section={section} />
          ))}
        </div>
      ) : (
        <EmptyState title="No world entities">
          The API returned no world entity sections for this preview.
        </EmptyState>
      )}
      <p className="evidence-note">{world.evidence_summary}</p>
    </section>
  );
}

function WorldEntitySection({ section }: { section: OutputSection }) {
  const items = readableOutputItems(section.items);
  return (
    <article className="profile-card">
      <header>
        <h3>{section.title}</h3>
      </header>
      {items.length > 0 ? (
        <ul className="world-item-list">
          {items.map((item, index) => (
            <li key={`${index}-${item}`}>{item}</li>
          ))}
        </ul>
      ) : (
        <p>Unknown</p>
      )}
    </article>
  );
}
