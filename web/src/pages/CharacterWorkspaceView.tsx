import { useMutation } from "@tanstack/react-query";
import { FormEvent, useState } from "react";

import { apiClient, type CharacterPreviewRequest } from "../api/client";
import type { CharacterPreview, CharacterProfile, OutputSection } from "../api/schemas";
import { EmptyState, ErrorMessage } from "../components/Feedback";
import { formatSceneScope } from "../formatting/display";
import {
  DeveloperPreviewToggle,
  ProjectOutputSummaryPanel,
} from "../output/ProjectOutputSummaryPanel";
import {
  buildCharacterPreviewPayload,
  canSubmitCharacterPreviewInput,
} from "../previewing/previewPayload";
import { readableOutputItems } from "../output/readableOutput";
import type { ProjectSummary } from "../projects/projectStore";

const DEFAULT_SOURCE_TEXT = "Chapter 1\n";
const DEFAULT_AI_RESPONSE =
  '{\n  "entities": [],\n  "facts": [],\n  "relationships": [],\n  "state_changes": []\n}';

export function CharacterWorkspaceView({ project }: { project: ProjectSummary }) {
  const [sourceId, setSourceId] = useState(project.id.replace(/^project_/, "source_"));
  const [filename, setFilename] = useState("chapter_001.txt");
  const [title, setTitle] = useState(project.name);
  const [sourceText, setSourceText] = useState(DEFAULT_SOURCE_TEXT);
  const [aiResponseText, setAiResponseText] = useState(DEFAULT_AI_RESPONSE);
  const [characterIdsText, setCharacterIdsText] = useState("");
  const [sceneId, setSceneId] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [previewResult, setPreviewResult] = useState<CharacterPreview | null>(null);

  const previewCharacters = useMutation({
    mutationFn: (payload: CharacterPreviewRequest) => apiClient.previewCharacters(payload),
    onSuccess(result) {
      setPreviewResult(result);
    },
    onError() {
      setPreviewResult(null);
    },
  });

  const canSubmit = canSubmitCharacterPreviewInput({
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
    previewCharacters.reset();
    try {
      const payload = buildCharacterPreviewPayload({
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
      previewCharacters.mutate(payload);
    } catch (error) {
      setPreviewResult(null);
      setFormError(error instanceof Error ? error.message : "Character preview form is invalid.");
    }
  }

  return (
    <div className="workspace-view-stack">
      <div>
        <p className="eyebrow">Characters</p>
        <h2>Characters</h2>
      </div>

      <ProjectOutputSummaryPanel project={project} surface="characters" />

      <DeveloperPreviewToggle>
        <section>
          <h2>Character Preview</h2>
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
            {previewCharacters.error ? (
              <ErrorMessage>{previewCharacters.error.message}</ErrorMessage>
            ) : null}
            <button
              type="submit"
              className="primary-button"
              disabled={!canSubmit || previewCharacters.isPending}
            >
              {previewCharacters.isPending ? "Building preview" : "Preview characters"}
            </button>
          </form>
        </section>
      </DeveloperPreviewToggle>

      {previewResult ? <CharacterPreviewResult result={previewResult} /> : null}
    </div>
  );
}

function CharacterPreviewResult({ result }: { result: CharacterPreview }) {
  return (
    <section className="project-panel" aria-label="Character preview result">
      <h2>Character Profiles</h2>
      <p className="result-summary">
        {result.character_profiles.length.toLocaleString()} character profile
        {result.character_profiles.length === 1 ? "" : "s"} for {formatSceneScope(result.scene_id)}.
      </p>
      {result.character_profiles.length > 0 ? (
        <div className="profile-grid">
          {result.character_profiles.map((profile) => (
            <CharacterProfileCard key={profile.character_id} profile={profile} />
          ))}
        </div>
      ) : (
        <EmptyState title="No character profiles">
          The API returned no character profiles for this preview.
        </EmptyState>
      )}
    </section>
  );
}

function CharacterProfileCard({ profile }: { profile: CharacterProfile }) {
  return (
    <article className="profile-card character-profile-card">
      <header className="character-profile-header">
        <div className="character-portrait" aria-hidden="true">
          {characterInitials(profile.display_name)}
        </div>
        <div>
          <h3>{profile.display_name}</h3>
          <p>{profile.subtitle}</p>
        </div>
      </header>
      <details className="profile-disclosure">
        <summary>Character details</summary>
        <div className="profile-section-grid">
          <ProfileSection section={profile.race} />
          <ProfileSection section={profile.gender} />
          <ProfileSection section={profile.status} />
          <ProfileSection section={profile.current_goal} />
          <ProfileSection section={profile.current_equipment} />
          <ProfileSection section={profile.current_abilities} />
          <ProfileSection section={profile.current_assets} />
          <ProfileSection section={profile.territory} />
          <ProfileSection section={profile.relationships} />
          <ProfileSection section={profile.current_limitations} />
          <ProfileSection section={profile.recent_changes} />
        </div>
      </details>
      <p className="evidence-note">{profile.evidence_summary}</p>
    </article>
  );
}

function characterInitials(name: string): string {
  const initials = name
    .split(/\s+/u)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
  return initials || "?";
}

function ProfileSection({ section }: { section: OutputSection }) {
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
