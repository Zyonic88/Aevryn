import { useMutation } from "@tanstack/react-query";
import { FormEvent, useState } from "react";

import { apiClient, type ScenePreviewRequest } from "../api/client";
import type { OutputSection, ScenePreview } from "../api/schemas";
import { ErrorMessage } from "../components/Feedback";
import { formatSceneScope } from "../formatting/display";
import {
  DeveloperPreviewToggle,
  ProjectOutputSummaryPanel,
} from "../output/ProjectOutputSummaryPanel";
import { readableOutputItems } from "../output/readableOutput";
import { buildScenePreviewPayload, canSubmitScenePreviewInput } from "../previewing/previewPayload";
import type { ProjectSummary } from "../projects/projectStore";

const DEFAULT_SOURCE_TEXT = "Chapter 1\n";
const DEFAULT_AI_RESPONSE =
  '{\n  "entities": [],\n  "facts": [],\n  "relationships": [],\n  "state_changes": []\n}';

export function SceneWorkspaceView({ project }: { project: ProjectSummary }) {
  const [sourceId, setSourceId] = useState(project.id.replace(/^project_/, "source_"));
  const [filename, setFilename] = useState("chapter_001.txt");
  const [title, setTitle] = useState(project.name);
  const [sourceText, setSourceText] = useState(DEFAULT_SOURCE_TEXT);
  const [aiResponseText, setAiResponseText] = useState(DEFAULT_AI_RESPONSE);
  const [characterIdsText, setCharacterIdsText] = useState("");
  const [sceneId, setSceneId] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [previewResult, setPreviewResult] = useState<ScenePreview | null>(null);

  const previewScene = useMutation({
    mutationFn: (payload: ScenePreviewRequest) => apiClient.previewScene(payload),
    onSuccess(result) {
      setPreviewResult(result);
    },
    onError() {
      setPreviewResult(null);
    },
  });

  const canSubmit = canSubmitScenePreviewInput({
    sourceId,
    filename,
    title,
    sourceText,
    aiResponseText,
    characterIdsText,
    sceneId,
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    previewScene.reset();
    try {
      const payload = buildScenePreviewPayload({
        sourceId,
        filename,
        title,
        sourceText,
        aiResponseText,
        characterIdsText,
        sceneId,
      });
      setFormError(null);
      setPreviewResult(null);
      previewScene.mutate(payload);
    } catch (error) {
      setPreviewResult(null);
      setFormError(error instanceof Error ? error.message : "Scene preview form is invalid.");
    }
  }

  return (
    <div className="workspace-view-stack">
      <div>
        <p className="eyebrow">Scenes</p>
        <h2>Scenes</h2>
      </div>

      <ProjectOutputSummaryPanel project={project} surface="scenes" />

      <DeveloperPreviewToggle>
        <section>
          <h2>Scene Preview</h2>
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
                Character IDs
                <input
                  value={characterIdsText}
                  onChange={(event) => setCharacterIdsText(event.target.value)}
                  placeholder="Optional: character_mark character_luna"
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
            {previewScene.error ? <ErrorMessage>{previewScene.error.message}</ErrorMessage> : null}
            <button
              type="submit"
              className="primary-button"
              disabled={!canSubmit || previewScene.isPending}
            >
              {previewScene.isPending ? "Building preview" : "Preview scene"}
            </button>
          </form>
        </section>
      </DeveloperPreviewToggle>

      {previewResult ? <ScenePreviewResult result={previewResult} /> : null}
    </div>
  );
}

function ScenePreviewResult({ result }: { result: ScenePreview }) {
  const scene = result.scene_sheet;
  return (
    <section className="project-panel" aria-label="Scene preview result">
      <h2>{scene.title}</h2>
      <p className="result-summary">
        {scene.chapter_label} for {formatSceneScope(result.scene_id)}.
      </p>
      <details className="profile-disclosure">
        <summary>Scene details</summary>
        <div className="profile-section-grid">
          <SceneSection section={scene.location} />
          <SceneSection section={scene.characters_present} />
          <SceneSection section={scene.mood} />
          <SceneSection section={scene.purpose} />
          <SceneSection section={scene.visual_highlights} />
          <SceneSection section={scene.continuity_changes} />
          <SceneSection section={scene.environment} />
        </div>
      </details>
      <p className="evidence-note">{scene.evidence_summary}</p>
    </section>
  );
}

function SceneSection({ section }: { section: OutputSection }) {
  const items = readableOutputItems(section.items);
  return (
    <section className="profile-section">
      <h4>{section.title}</h4>
      {items.length > 0 ? (
        <ul>
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : (
        <p>Unknown</p>
      )}
    </section>
  );
}
