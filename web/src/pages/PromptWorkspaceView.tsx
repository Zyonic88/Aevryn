import { useMutation } from "@tanstack/react-query";
import { FormEvent, useState } from "react";

import { apiClient, type PromptPreviewRequest } from "../api/client";
import type { OutputSection, PromptPreview } from "../api/schemas";
import { ErrorMessage } from "../components/Feedback";
import { formatSceneScope } from "../formatting/display";
import {
  DeveloperPreviewToggle,
  ProjectOutputSummaryPanel,
} from "../output/ProjectOutputSummaryPanel";
import {
  buildPromptPreviewPayload,
  canSubmitPromptPreviewInput,
} from "../previewing/previewPayload";
import {
  readablePromptPreview,
  readablePromptSummary,
  readablePromptText,
} from "../output/readableOutput";
import type { ProjectSummary } from "../projects/projectStore";

const DEFAULT_SOURCE_TEXT = "Chapter 1\n";
const DEFAULT_AI_RESPONSE =
  '{\n  "entities": [],\n  "facts": [],\n  "relationships": [],\n  "state_changes": []\n}';

export function PromptWorkspaceView({ project }: { project: ProjectSummary }) {
  const [sourceId, setSourceId] = useState(project.id.replace(/^project_/, "source_"));
  const [filename, setFilename] = useState("chapter_001.txt");
  const [title, setTitle] = useState(project.name);
  const [sourceText, setSourceText] = useState(DEFAULT_SOURCE_TEXT);
  const [aiResponseText, setAiResponseText] = useState(DEFAULT_AI_RESPONSE);
  const [characterIdsText, setCharacterIdsText] = useState("");
  const [sceneId, setSceneId] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [previewResult, setPreviewResult] = useState<PromptPreview | null>(null);

  const previewPrompts = useMutation({
    mutationFn: (payload: PromptPreviewRequest) => apiClient.previewPrompts(payload),
    onSuccess(result) {
      setPreviewResult(result);
    },
    onError() {
      setPreviewResult(null);
    },
  });

  const canSubmit = canSubmitPromptPreviewInput({
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
    previewPrompts.reset();
    try {
      const payload = buildPromptPreviewPayload({
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
      previewPrompts.mutate(payload);
    } catch (error) {
      setPreviewResult(null);
      setFormError(error instanceof Error ? error.message : "Prompt pack preview form is invalid.");
    }
  }

  return (
    <div className="workspace-view-stack">
      <div>
        <p className="eyebrow">Prompt Packs</p>
        <h2>Prompt Packs</h2>
      </div>

      <ProjectOutputSummaryPanel project={project} surface="prompts" />

      <DeveloperPreviewToggle>
        <section>
          <h2>Prompt Pack Preview</h2>
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
            {previewPrompts.error ? (
              <ErrorMessage>{previewPrompts.error.message}</ErrorMessage>
            ) : null}
            <button
              type="submit"
              className="primary-button"
              disabled={!canSubmit || previewPrompts.isPending}
            >
              {previewPrompts.isPending ? "Building preview" : "Preview prompt pack"}
            </button>
          </form>
        </section>
      </DeveloperPreviewToggle>

      {previewResult ? <PromptPreviewResult result={previewResult} /> : null}
    </div>
  );
}

function PromptPreviewResult({ result }: { result: PromptPreview }) {
  const pack = result.production_pack;
  return (
    <section className="project-panel" aria-label="Prompt pack preview result">
      <h2>Production Pack</h2>
      <p className="result-summary">
        {pack.scene.title} for {formatSceneScope(result.scene_id)}.
      </p>
      <div className="prompt-pack-grid">
        <PromptSection section={pack.image_prompt} />
        <PromptSection section={pack.narration_prompt} />
        <PromptSection section={pack.camera_prompt} />
        <PromptSection section={pack.animation_prompt} />
      </div>
      <section className="profile-section prompt-scene-context">
        <h4>Scene Context</h4>
        <p>
          {pack.scene.chapter_label} / {formatSceneScope(pack.scene.scene_id)}
        </p>
        <p className="evidence-note">{pack.scene.evidence_summary}</p>
      </section>
    </section>
  );
}

function PromptSection({ section }: { section: OutputSection }) {
  const [copyState, setCopyState] = useState<"idle" | "copied" | "failed">("idle");
  const promptText = readablePromptText(section);
  const promptSummary = readablePromptSummary(section);
  const promptPreview = readablePromptPreview(section, { maxItems: 3 });

  async function copyPrompt() {
    const clipboard = navigator.clipboard;
    if (!clipboard) {
      setCopyState("failed");
      return;
    }
    try {
      await clipboard.writeText(promptText);
      setCopyState("copied");
    } catch {
      setCopyState("failed");
    }
  }

  return (
    <section className="profile-section prompt-text-section">
      <div className="prompt-section-heading">
        <h4>{section.title}</h4>
        <div className="prompt-copy-controls">
          {copyState === "copied" ? <span>Copied</span> : null}
          {copyState === "failed" ? <span>Copy unavailable</span> : null}
          <button
            type="button"
            className="text-button"
            aria-label={`Copy ${section.title}`}
            onClick={() => void copyPrompt()}
          >
            Copy
          </button>
        </div>
      </div>
      <ul className="prompt-preview-list" aria-label={`${section.title} preview`}>
        {promptPreview.items.length > 0 ? (
          promptPreview.items.map((item) => <li key={item}>{item}</li>)
        ) : (
          <li>Unknown.</li>
        )}
      </ul>
      {promptPreview.hiddenCount > 0 ? (
        <p className="prompt-preview-overflow">
          {promptPreview.hiddenCount.toLocaleString()} more prompt{" "}
          {promptPreview.hiddenCount === 1 ? "detail" : "details"} inside.
        </p>
      ) : null}
      <details className="prompt-disclosure" aria-label={`${section.title} prompt body`}>
        <summary>
          Show {section.title} - {promptSummary}
        </summary>
        <p>{promptText}</p>
      </details>
    </section>
  );
}
