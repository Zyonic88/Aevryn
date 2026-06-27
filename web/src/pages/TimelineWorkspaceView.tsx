import { useMutation } from "@tanstack/react-query";
import { FormEvent, useState } from "react";

import { apiClient, type TimelinePreviewRequest } from "../api/client";
import type { SceneMapEntry, TimelinePreview } from "../api/schemas";
import { EmptyState, ErrorMessage } from "../components/Feedback";
import {
  buildTimelinePreviewPayload,
  canSubmitTimelinePreviewInput,
} from "../previewing/previewPayload";
import type { ProjectSummary } from "../projects/projectStore";

const DEFAULT_SOURCE_TEXT = "Chapter 1\n";
const DEFAULT_AI_RESPONSE =
  '{\n  "entities": [],\n  "facts": [],\n  "relationships": [],\n  "state_changes": []\n}';

export function TimelineWorkspaceView({ project }: { project: ProjectSummary }) {
  const [sourceId, setSourceId] = useState(project.id.replace(/^project_/, "source_"));
  const [filename, setFilename] = useState("chapter_001.txt");
  const [title, setTitle] = useState(project.name);
  const [sourceText, setSourceText] = useState(DEFAULT_SOURCE_TEXT);
  const [aiResponseText, setAiResponseText] = useState(DEFAULT_AI_RESPONSE);
  const [sceneId, setSceneId] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [previewResult, setPreviewResult] = useState<TimelinePreview | null>(null);

  const previewTimeline = useMutation({
    mutationFn: (payload: TimelinePreviewRequest) => apiClient.previewTimeline(payload),
    onSuccess(result) {
      setPreviewResult(result);
    },
    onError() {
      setPreviewResult(null);
    },
  });

  const canSubmit = canSubmitTimelinePreviewInput({
    sourceId,
    filename,
    title,
    sourceText,
    aiResponseText,
    sceneId,
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      const payload = buildTimelinePreviewPayload({
        sourceId,
        filename,
        title,
        sourceText,
        aiResponseText,
        sceneId,
      });
      setFormError(null);
      setPreviewResult(null);
      previewTimeline.mutate(payload);
    } catch (error) {
      setPreviewResult(null);
      setFormError(error instanceof Error ? error.message : "Timeline preview form is invalid.");
    }
  }

  return (
    <div className="workspace-view-stack">
      <div>
        <p className="eyebrow">Timeline</p>
        <h2>Timeline</h2>
      </div>

      <section className="project-panel">
        <h2>Timeline Preview</h2>
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
          <label>
            Scene ID
            <input
              value={sceneId}
              onChange={(event) => setSceneId(event.target.value)}
              placeholder="Optional scene ID"
            />
          </label>
          {formError ? <ErrorMessage>{formError}</ErrorMessage> : null}
          {previewTimeline.error ? <ErrorMessage>{previewTimeline.error.message}</ErrorMessage> : null}
          <button
            type="submit"
            className="primary-button"
            disabled={!canSubmit || previewTimeline.isPending}
          >
            {previewTimeline.isPending ? "Building preview" : "Preview timeline"}
          </button>
        </form>
      </section>

      {previewResult ? <TimelinePreviewResult result={previewResult} /> : null}
    </div>
  );
}

function TimelinePreviewResult({ result }: { result: TimelinePreview }) {
  return (
    <section className="project-panel" aria-label="Timeline preview result">
      <h2>Timeline Order</h2>
      <p className="result-summary">
        Current scene {result.current_scene_id} across {result.chapter_ids.length.toLocaleString()}{" "}
        chapter{result.chapter_ids.length === 1 ? "" : "s"}.
      </p>
      <dl className="metric-grid">
        <div>
          <dt>Format</dt>
          <dd>{result.source_format}</dd>
        </div>
        <div>
          <dt>Scenes</dt>
          <dd>{result.scene_map.length}</dd>
        </div>
        <div>
          <dt>State changes</dt>
          <dd>{result.accepted_state_change_ids.length}</dd>
        </div>
      </dl>
      {result.scene_map.length > 0 ? (
        <div className="timeline-list" aria-label="Timeline scene map">
          {result.scene_map.map((scene) => (
            <TimelineSceneRow
              key={scene.scene_id}
              scene={scene}
              isCurrent={scene.scene_id === result.current_scene_id}
            />
          ))}
        </div>
      ) : (
        <EmptyState title="No timeline scenes">
          The API returned no scene order entries for this preview.
        </EmptyState>
      )}
      {result.accepted_state_change_ids.length > 0 ? (
        <section className="profile-section">
          <h4>Accepted State Changes</h4>
          <ul>
            {result.accepted_state_change_ids.map((stateChangeId) => (
              <li key={stateChangeId}>{stateChangeId}</li>
            ))}
          </ul>
        </section>
      ) : (
        <EmptyState title="No state changes">
          The API returned no accepted state-change IDs for this preview.
        </EmptyState>
      )}
    </section>
  );
}

function TimelineSceneRow({
  scene,
  isCurrent,
}: {
  scene: SceneMapEntry;
  isCurrent: boolean;
}) {
  return (
    <article className={isCurrent ? "timeline-row timeline-row-current" : "timeline-row"}>
      <div>
        <strong>{scene.title}</strong>
        <span>{scene.scene_id}</span>
      </div>
      <p>
        Chapter {scene.chapter_index}, Scene {scene.scene_index}
      </p>
      {isCurrent ? <span className="timeline-current-label">Current</span> : null}
    </article>
  );
}
