import { useMutation } from "@tanstack/react-query";
import { FormEvent, useState } from "react";

import { apiClient, type ContinuityPreviewRequest } from "../api/client";
import type { ContinuityPreview, ContinuityRecord, ContinuityScene } from "../api/schemas";
import { EmptyState, ErrorMessage } from "../components/Feedback";
import {
  buildContinuityPreviewPayload,
  canSubmitContinuityPreviewInput,
} from "../previewing/previewPayload";
import type { ProjectSummary } from "../projects/projectStore";

const DEFAULT_SOURCE_TEXT = "Chapter 1\n";
const DEFAULT_AI_RESPONSE =
  '{\n  "entities": [],\n  "facts": [],\n  "relationships": [],\n  "state_changes": []\n}';

const bucketLabels = {
  new: "New",
  updated: "Updated",
  still_known: "Still Known",
  invalidated: "Invalidated",
} as const;

type ContinuityBucketKey = keyof typeof bucketLabels;

export function ContinuityWorkspaceView({ project }: { project: ProjectSummary }) {
  const [sourceId, setSourceId] = useState(project.id.replace(/^project_/, "source_"));
  const [filename, setFilename] = useState("chapter_001.txt");
  const [title, setTitle] = useState(project.name);
  const [sourceText, setSourceText] = useState(DEFAULT_SOURCE_TEXT);
  const [aiResponseText, setAiResponseText] = useState(DEFAULT_AI_RESPONSE);
  const [sceneId, setSceneId] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [previewResult, setPreviewResult] = useState<ContinuityPreview | null>(null);

  const previewContinuity = useMutation({
    mutationFn: (payload: ContinuityPreviewRequest) => apiClient.previewContinuity(payload),
    onSuccess(result) {
      setPreviewResult(result);
    },
    onError() {
      setPreviewResult(null);
    },
  });

  const canSubmit = canSubmitContinuityPreviewInput({
    sourceId,
    filename,
    title,
    sourceText,
    aiResponseText,
    sceneId,
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    previewContinuity.reset();
    try {
      const payload = buildContinuityPreviewPayload({
        sourceId,
        filename,
        title,
        sourceText,
        aiResponseText,
        sceneId,
      });
      setFormError(null);
      setPreviewResult(null);
      previewContinuity.mutate(payload);
    } catch (error) {
      setPreviewResult(null);
      setFormError(
        error instanceof Error ? error.message : "Continuity preview form is invalid.",
      );
    }
  }

  return (
    <div className="workspace-view-stack">
      <div>
        <p className="eyebrow">Continuity</p>
        <h2>Continuity</h2>
      </div>

      <section className="project-panel">
        <h2>Continuity Preview</h2>
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
          <label>
            Scene ID
            <input
              value={sceneId}
              onChange={(event) => setSceneId(event.target.value)}
              placeholder="Optional scene ID"
            />
          </label>
          {formError ? <ErrorMessage>{formError}</ErrorMessage> : null}
          {previewContinuity.error ? (
            <ErrorMessage>{previewContinuity.error.message}</ErrorMessage>
          ) : null}
          <button
            type="submit"
            className="primary-button"
            disabled={!canSubmit || previewContinuity.isPending}
          >
            {previewContinuity.isPending ? "Building preview" : "Preview continuity"}
          </button>
        </form>
      </section>

      {previewResult ? <ContinuityPreviewResult result={previewResult} /> : null}
    </div>
  );
}

function ContinuityPreviewResult({ result }: { result: ContinuityPreview }) {
  const scenes = result.continuity_report.scenes;
  return (
    <section className="project-panel" aria-label="Continuity preview result">
      <h2>Continuity Report</h2>
      <p className="result-summary">
        {scenes.length.toLocaleString()} scene{scenes.length === 1 ? "" : "s"} for{" "}
        {result.continuity_report.source_id}.
      </p>
      {scenes.length > 0 ? (
        <div className="continuity-scene-list">
          {scenes.map((scene) => (
            <ContinuitySceneCard key={scene.scene_id} scene={scene} />
          ))}
        </div>
      ) : (
        <EmptyState title="No continuity scenes">
          The API returned no continuity scene entries for this preview.
        </EmptyState>
      )}
    </section>
  );
}

function ContinuitySceneCard({ scene }: { scene: ContinuityScene }) {
  return (
    <article className="profile-card">
      <header>
        <p className="eyebrow">Scene</p>
        <h3>{scene.scene_id}</h3>
      </header>
      <dl className="metric-grid continuity-metrics">
        {bucketKeys().map((bucket) => (
          <div key={bucket}>
            <dt>{bucketLabels[bucket]}</dt>
            <dd>{scene[bucket].length}</dd>
          </div>
        ))}
      </dl>
      <div className="profile-section-grid">
        {bucketKeys().map((bucket) => (
          <ContinuityBucket
            key={bucket}
            title={bucketLabels[bucket]}
            records={scene[bucket]}
          />
        ))}
      </div>
    </article>
  );
}

function ContinuityBucket({
  title,
  records,
}: {
  title: string;
  records: ContinuityRecord[];
}) {
  return (
    <section className="profile-section">
      <h4>{title}</h4>
      {records.length > 0 ? (
        <ul>
          {records.map((record) => (
            <li key={record.record_id}>
              <strong>{record.record_type}</strong>: {record.description}
              <span className="continuity-evidence">
                {record.chapter_id} / {record.scene_id} / {record.evidence_id}
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p>Unknown</p>
      )}
    </section>
  );
}

function bucketKeys(): ContinuityBucketKey[] {
  return ["new", "updated", "still_known", "invalidated"];
}
