import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent, type ReactNode } from "react";

import { apiClient, type ProjectCorrectionRequest } from "../api/client";
import type {
  CharacterProfile,
  ContinuityReport,
  OutputSection,
  ProductionPack,
  ProjectExportOption,
  ProjectOutputs,
  ProjectOutputSurface,
  ProjectTimelineChange,
  SceneSheet,
  WorldSheet,
} from "../api/schemas";
import { useAuth } from "../auth/useAuth";
import { EmptyState, ErrorMessage, LoadingMessage } from "../components/Feedback";
import { formatDateTime, formatRunStatus, formatSceneScope } from "../formatting/display";
import type { ProjectSummary } from "../projects/projectStore";
import {
  compactIdentityReviewItems,
  identityReviewDetails,
  identityReviewKey,
  identityReviewTitle,
  reviewItemCountLabel,
} from "./languageIdentityDisplay";
import {
  isInternalOutputPlaceholder,
  readableOutputItems,
  readableOutputText,
  readablePromptPreview,
  readablePromptSummary,
  readablePromptText,
} from "./readableOutput";
import { downloadPromptText } from "./promptDownload";

type OutputSurface =
  "characters" | "world" | "timeline" | "scenes" | "continuity" | "prompts" | "exports";

const MAX_VISIBLE_PROMPT_SCENES = 24;
const MAX_VISIBLE_PROMPT_DETAILS = 10;
const CHARACTER_CARD_PAGE_SIZE = 48;
const WORLD_CARD_PAGE_SIZE = 48;
const TIMELINE_GROUP_PAGE_SIZE = 60;
const SCENE_CARD_PAGE_SIZE = 48;
const CONTINUITY_SCENE_PAGE_SIZE = 24;
const CHARACTER_CORRECTION_FIELDS = [
  { field: "race", label: "Race" },
  { field: "gender", label: "Gender" },
  { field: "appearance", label: "Appearance" },
  { field: "status", label: "Status" },
  { field: "current_goal", label: "Current goal" },
  { field: "current_equipment", label: "Current equipment" },
  { field: "current_abilities", label: "Current abilities" },
  { field: "current_assets", label: "Current assets" },
  { field: "territory", label: "Territory" },
  { field: "relationships", label: "Relationships" },
  { field: "current_limitations", label: "Current limitations" },
  { field: "recent_changes", label: "Recent changes" },
] as const;
const WORLD_CORRECTION_FIELDS = [
  { field: "classification", label: "Classification" },
  { field: "display_name", label: "Display name" },
  { field: "description", label: "Description" },
  { field: "condition", label: "Condition" },
  { field: "location", label: "Location" },
  { field: "relationships", label: "Relationships" },
  { field: "notes", label: "Notes" },
] as const;
const CHARACTER_RECENT_CHANGE_PROFILE_LABELS = new Set([
  "alias",
  "appearance",
  "description",
  "gender",
  "name",
  "race",
  "title",
]);

export function ProjectOutputSummaryPanel({
  project,
  surface,
}: {
  project: ProjectSummary;
  surface: OutputSurface;
}) {
  const { session } = useAuth();
  const outputsQuery = useQuery({
    queryKey: projectOutputsQueryKey(project.id, session?.session_token),
    queryFn: () => apiClient.projectOutputs(project.id, requireSessionToken(session), nowUtc()),
    enabled: Boolean(session?.session_token),
  });

  if (outputsQuery.isLoading) {
    return <LoadingMessage>Loading processed project results.</LoadingMessage>;
  }
  if (outputsQuery.error) {
    return (
      <EmptyState title="Processed output unavailable">
        Aevryn could not load processed project results for this workspace.
      </EmptyState>
    );
  }
  if (!outputsQuery.data) {
    return (
      <EmptyState title="No project output">
        Process a saved import to create project output for this workspace.
      </EmptyState>
    );
  }
  return (
    <ProjectOutputSummary
      outputs={outputsQuery.data}
      projectId={project.id}
      sessionToken={session?.session_token ?? ""}
      surface={surface}
    />
  );
}

export function DeveloperPreviewToggle({ children }: { children: ReactNode }) {
  return (
    <details className="project-panel">
      <summary>Advanced preview</summary>
      <div className="workspace-view-stack developer-preview-stack">{children}</div>
    </details>
  );
}

function ProjectOutputSummary({
  outputs,
  projectId,
  sessionToken,
  surface,
}: {
  outputs: ProjectOutputs;
  projectId: string;
  sessionToken: string;
  surface: OutputSurface;
}) {
  const surfaceSummary = outputs.surfaces.find((item) => item.surface === surface);
  if (!outputs.canon.available || !surfaceSummary) {
    const processingActive = outputs.status === "pending" || outputs.status === "running";
    return (
      <section className="project-panel" aria-label="Processed project output">
        <h2>Processed Project Results</h2>
        <EmptyState
          title={processingActive ? "Processing project output" : "No processed output yet"}
        >
          {processingActive
            ? "Aevryn is processing this import. Results will appear here when the canon snapshot is ready."
            : "Save an import, submit processing, and wait for a canon snapshot."}
        </EmptyState>
      </section>
    );
  }
  const visibleSurfaceCount = surfaceDisplayItemCount(surface, outputs, surfaceSummary);

  return (
    <section className="project-panel output-summary-panel" aria-label="Processed project output">
      <header className="surface-heading">
        <div>
          <p className="eyebrow">{surfaceEyebrow(surface)}</p>
          <h2>{surfaceSummary.title}</h2>
          <p className="result-summary">{surfaceSummary.summary}</p>
        </div>
        <span className="surface-count-badge">
          {visibleSurfaceCount.toLocaleString()}{" "}
          {surfaceItemLabel(surface, visibleSurfaceCount)}
        </span>
      </header>
      <OutputMetadataDisclosure
        outputs={outputs}
        itemCount={visibleSurfaceCount}
        surfaceSummary={surfaceSummary}
        surface={surface}
      />
      {surface === "characters" && hasIdentityReviewItems(outputs) ? (
        <IdentityReviewPanel outputs={outputs} defaultOpen={false} />
      ) : null}
      <ReadableSurfacePanels
        surface={surface}
        outputs={outputs}
        projectId={projectId}
        sessionToken={sessionToken}
      />
      {surfaceSummary.status === "waiting" ? (
        <EmptyState title="No extracted canon content yet">
          This project has imported chapter and scene structure, but this output needs accepted
          extraction data before it can show creator-facing content.
        </EmptyState>
      ) : null}
    </section>
  );
}

function OutputMetadataDisclosure({
  itemCount,
  outputs,
  surface,
  surfaceSummary,
}: {
  itemCount: number;
  outputs: ProjectOutputs;
  surface: OutputSurface;
  surfaceSummary: ProjectOutputSurface;
}) {
  const runStatus = outputs.latest_engine_run
    ? formatRunStatus(outputs.latest_engine_run.status)
    : "No run";
  return (
    <details className="output-metadata-disclosure">
      <summary>
        <span>Canon metadata</span>
        {" "}
        <span>
          {runStatus} | {outputs.canon.chapters.toLocaleString()} chapters |{" "}
          {outputs.canon.scenes.toLocaleString()} scenes |{" "}
          {outputs.canon.evidence_anchor_count.toLocaleString()} evidence
        </span>
      </summary>
      <div className="workspace-view-stack output-metadata-body">
        <dl className="metric-grid">
          <Metric label="State" value={formatRunStatus(surfaceSummary.status)} />
          <Metric label="Items" value={itemCount.toLocaleString()} />
          <Metric label="Import" value={outputs.latest_import ? "Latest import" : "No import"} />
          <Metric label="Run" value={runStatus} />
          <Metric label="Chapters" value={outputs.canon.chapters.toLocaleString()} />
          <Metric label="Scenes" value={outputs.canon.scenes.toLocaleString()} />
          <Metric label="Evidence" value={outputs.canon.evidence_anchor_count.toLocaleString()} />
          <Metric label="Snapshot" value={formatDateTime(outputs.canon.created_at)} />
        </dl>
        <LanguageIdentityStatus outputs={outputs} />
        <SurfaceDetails surface={surface} outputs={outputs} surfaceSummary={surfaceSummary} />
      </div>
    </details>
  );
}

function surfaceDisplayItemCount(
  surface: OutputSurface,
  outputs: ProjectOutputs,
  surfaceSummary: ProjectOutputSurface,
): number {
  if (surface === "characters") {
    return mergeCharacterProfiles(outputs.character_profiles).length;
  }
  if (surface === "world") {
    return outputs.world_sheet?.entity_sections.length ?? 0;
  }
  return surfaceSummary.item_count;
}

function surfaceEyebrow(surface: OutputSurface): string {
  if (surface === "prompts") {
    return "Production";
  }
  if (surface === "exports") {
    return "Delivery";
  }
  return "Canon surface";
}

function surfaceItemLabel(surface: OutputSurface, count = 2): string {
  if (surface === "characters") {
    return count === 1 ? "profile" : "profiles";
  }
  if (surface === "world") {
    return count === 1 ? "entry" : "entries";
  }
  if (surface === "timeline") {
    return count === 1 ? "change" : "changes";
  }
  if (surface === "scenes" || surface === "prompts") {
    return count === 1 ? "scene" : "scenes";
  }
  if (surface === "exports") {
    return count === 1 ? "option" : "options";
  }
  return "records";
}

function hasIdentityReviewItems(outputs: ProjectOutputs): boolean {
  const summary = outputs.language_identity;
  return summary.identity_ambiguous_count + summary.identity_unresolved_count > 0;
}

function LanguageIdentityStatus({ outputs }: { outputs: ProjectOutputs }) {
  const summary = outputs.language_identity;
  const hasPhase12Metadata =
    summary.translation_unit_count > 0 || summary.identity_decision_count > 0;
  if (!hasPhase12Metadata) {
    return null;
  }
  const identityDetails = [
    `${summary.identity_resolved_count.toLocaleString()} resolved`,
    `${summary.identity_ambiguous_count.toLocaleString()} ambiguous`,
    `${summary.identity_unresolved_count.toLocaleString()} unresolved`,
  ].join(" / ");
  const translationStatus =
    summary.translation_review_count > 0
      ? reviewItemCountLabel(summary.translation_review_count)
      : "No review items";
  const identityReviewCount = summary.identity_ambiguous_count + summary.identity_unresolved_count;
  const identityReviewStatus =
    identityReviewCount > 0
      ? `${reviewItemCountLabel(identityReviewCount)} need character review`
      : "No character review items";
  const reviewStatus =
    summary.translation_review_count > 0 && identityReviewCount > 0
      ? `${translationStatus}; ${identityReviewStatus}`
      : summary.translation_review_count > 0
        ? translationStatus
        : identityReviewStatus;
  return (
    <div
      className="compact-list language-identity-status"
      aria-label="Language and identity status"
    >
      <div className="compact-row">
        <strong>Language</strong>
        <span>
          {summary.translation_unit_count.toLocaleString()} normalized scenes; {translationStatus}
        </span>
      </div>
      <div className="compact-row">
        <strong>Identity</strong>
        <span>
          {summary.identity_decision_count.toLocaleString()} reference decisions; {identityDetails}
        </span>
      </div>
      <div className="compact-row">
        <strong>Review</strong>
        <span>{reviewStatus}</span>
      </div>
    </div>
  );
}

function identityReviewAction(status: string): string {
  if (status === "ambiguous") {
    return "Aevryn did not merge this reference";
  }
  if (status === "unresolved") {
    return "Aevryn left this reference unresolved";
  }
  return "Aevryn marked this reference for review";
}

function IdentityReviewPanel({
  outputs,
  defaultOpen,
}: {
  outputs: ProjectOutputs;
  defaultOpen: boolean;
}) {
  const [statusFilter, setStatusFilter] = useState<"all" | "ambiguous" | "unresolved">("all");
  const summary = outputs.language_identity;
  const reviewTotal = summary.identity_ambiguous_count + summary.identity_unresolved_count;
  const reviewItems = compactIdentityReviewItems(summary.identity_review_items, 24);
  const filteredItems =
    statusFilter === "all"
      ? reviewItems
      : reviewItems.filter((item) => item.status === statusFilter);

  if (summary.identity_decision_count === 0) {
    return null;
  }

  return (
    <details className="identity-review-panel" open={defaultOpen}>
      <summary>Identity Review</summary>
      <section aria-label="Identity review">
        <div className="identity-review-heading">
          <div>
            <h3>Identity Review</h3>
            <p>
              {summary.identity_resolved_count.toLocaleString()} resolved,{" "}
              {summary.identity_ambiguous_count.toLocaleString()} ambiguous,{" "}
              {summary.identity_unresolved_count.toLocaleString()} unresolved.
            </p>
          </div>
          <div className="segmented-control" aria-label="Identity review filter">
            <button
              type="button"
              aria-pressed={statusFilter === "all"}
              onClick={() => setStatusFilter("all")}
            >
              All
            </button>
            <button
              type="button"
              aria-pressed={statusFilter === "ambiguous"}
              onClick={() => setStatusFilter("ambiguous")}
            >
              Ambiguous
            </button>
            <button
              type="button"
              aria-pressed={statusFilter === "unresolved"}
              onClick={() => setStatusFilter("unresolved")}
            >
              Unresolved
            </button>
          </div>
        </div>
        {reviewTotal > reviewItems.length ? (
          <p className="result-summary">
            Showing {reviewItems.length.toLocaleString()} representative review examples from{" "}
            {reviewTotal.toLocaleString()} references that need attention.
          </p>
        ) : null}
        {filteredItems.length > 0 ? (
          <div className="compact-list">
            {filteredItems.map((item) => (
              <div className="compact-row identity-review-row" key={identityReviewKey(item)}>
                <strong>{identityReviewTitle(item)}</strong>
                <span>{identityReviewDetails(item, identityReviewAction(item.status))}</span>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState title="No matching identity reviews">
            No identity review examples match this filter.
          </EmptyState>
        )}
      </section>
    </details>
  );
}

function ReadableSurfacePanels({
  surface,
  outputs,
  projectId,
  sessionToken,
}: {
  surface: OutputSurface;
  outputs: ProjectOutputs;
  projectId: string;
  sessionToken: string;
}) {
  if (surface === "characters" && outputs.character_profiles.length > 0) {
    const characterProfiles = mergeCharacterProfiles(outputs.character_profiles);
    return (
      <CharacterPanels
        profiles={characterProfiles}
        projectId={projectId}
        sessionToken={sessionToken}
      />
    );
  }
  if (
    surface === "world" &&
    outputs.world_sheet &&
    outputs.world_sheet.entity_sections.length > 0
  ) {
    return (
      <WorldPanel
        world={outputs.world_sheet}
        projectId={projectId}
        sessionToken={sessionToken}
      />
    );
  }
  if (surface === "timeline" && outputs.timeline_changes.length > 0) {
    return <TimelinePanel changes={outputs.timeline_changes} />;
  }
  if (surface === "scenes" && outputs.scene_sheets.length > 0) {
    return <SceneSheetsPanel scenes={outputs.scene_sheets} />;
  }
  if (surface === "continuity" && outputs.continuity_report) {
    return <ContinuityPanel report={outputs.continuity_report} />;
  }
  if (surface === "prompts" && outputs.prompt_packs.length > 0) {
    return <PromptPacksPanel packs={outputs.prompt_packs} />;
  }
  if (surface === "exports" && outputs.export_options.length > 0) {
    return <ExportOptionsPanel options={outputs.export_options} />;
  }
  return null;
}

function mergeCharacterProfiles(profiles: CharacterProfile[]): CharacterProfile[] {
  const profilesByName = new Map<string, CharacterProfile>();
  for (const profile of profiles) {
    const existingProfile = profilesByName.get(profile.display_name);
    if (!existingProfile) {
      profilesByName.set(profile.display_name, profile);
      continue;
    }
    profilesByName.set(profile.display_name, {
      ...existingProfile,
      subtitle: bestSubtitle(existingProfile.subtitle, profile.subtitle),
      aliases: mergeSection(existingProfile.aliases, profile.aliases),
      titles: mergeSection(existingProfile.titles, profile.titles),
      descriptions: mergeSection(existingProfile.descriptions, profile.descriptions),
      appearance: mergeSection(existingProfile.appearance, profile.appearance),
      race: mergeSection(existingProfile.race, profile.race),
      gender: mergeSection(existingProfile.gender, profile.gender),
      status: mergeSection(existingProfile.status, profile.status),
      current_goal: mergeSection(existingProfile.current_goal, profile.current_goal),
      current_equipment: mergeSection(existingProfile.current_equipment, profile.current_equipment),
      current_abilities: mergeSection(existingProfile.current_abilities, profile.current_abilities),
      current_assets: mergeSection(existingProfile.current_assets, profile.current_assets),
      territory: mergeSection(existingProfile.territory, profile.territory),
      relationships: mergeSection(existingProfile.relationships, profile.relationships),
      current_limitations: mergeSection(
        existingProfile.current_limitations,
        profile.current_limitations,
      ),
      first_appearance: mergeSection(existingProfile.first_appearance, profile.first_appearance),
      latest_appearance: mergeSection(existingProfile.latest_appearance, profile.latest_appearance),
      timeline_history: mergeSection(existingProfile.timeline_history, profile.timeline_history),
      evidence_references: mergeSection(
        existingProfile.evidence_references,
        profile.evidence_references,
      ),
      recent_changes: mergeSection(existingProfile.recent_changes, profile.recent_changes),
      evidence_summary: mergedEvidenceSummary(
        existingProfile.evidence_summary,
        profile.evidence_summary,
      ),
    });
  }
  return Array.from(profilesByName.values());
}

function bestSubtitle(left: string, right: string): string {
  const readableLeft = readableCharacterSubtitle(left);
  if (readableLeft !== "Unknown") {
    return left;
  }
  return readableCharacterSubtitle(right) !== "Unknown" ? right : readableLeft;
}

function mergeSection(left: OutputSection, right: OutputSection): OutputSection {
  return {
    title: left.title,
    items: readableOutputItems([...left.items, ...right.items]),
  };
}

function mergedEvidenceSummary(left: string, right: string): string {
  const factCount = evidenceFactCount(left) + evidenceFactCount(right);
  if (factCount > 0) {
    return `${factCount.toLocaleString()} verified facts`;
  }
  if (left === right) {
    return left;
  }
  return Array.from(new Set([left, right])).join("; ");
}

function CharacterPanel({
  profile,
  projectId,
  sessionToken,
}: {
  profile: CharacterProfile;
  projectId: string;
  sessionToken: string;
}) {
  const recentChanges = characterRecentChanges(profile);
  const displayName = readableCharacterName(profile.display_name);
  const subtitle = readableCharacterSubtitle(profile.subtitle);
  return (
    <article className="profile-card character-profile-card">
      <header className="character-profile-header">
        <div className="character-portrait" aria-hidden="true">
          {characterInitials(displayName)}
        </div>
        <div>
          <h3>{displayName}</h3>
          <p>{subtitle}</p>
        </div>
      </header>
      <CharacterAtAGlance profile={profile} />
      <CharacterIdentitySignals profile={profile} />
      <details className="profile-disclosure">
        <summary>Character details</summary>
        <div className="profile-section-grid character-detail-grid">
          <PanelSection section={profile.aliases} />
          <PanelSection section={profile.titles} />
          <PanelSection section={profile.descriptions} />
          <PanelSection section={profile.appearance} />
          <PanelSection section={profile.race} />
          <PanelSection section={profile.gender} />
          <PanelSection section={profile.status} />
          <PanelSection section={profile.current_goal} />
          <PanelSection section={profile.current_equipment} />
          <PanelSection section={profile.current_abilities} />
          <PanelSection section={profile.current_assets} />
          <PanelSection section={profile.territory} />
          <PanelSection section={profile.relationships} />
          <PanelSection section={profile.current_limitations} />
          <PanelSection section={profile.first_appearance} />
          <PanelSection section={profile.latest_appearance} />
          <PanelSection section={profile.timeline_history} />
          <PanelSection section={profile.evidence_references} />
          <PanelSection section={recentChanges} />
        </div>
      </details>
      <CorrectionEditor
        correctionKind="character"
        fieldOptions={CHARACTER_CORRECTION_FIELDS}
        projectId={projectId}
        sessionToken={sessionToken}
        targetId={profile.character_id}
        targetLabel={displayName}
      />
      <p className="evidence-note">{profile.evidence_summary}</p>
    </article>
  );
}

function CharacterIdentitySignals({ profile }: { profile: CharacterProfile }) {
  const signals = [
    characterSignal("Aliases", profile.aliases),
    characterSignal("Titles", profile.titles),
    characterSignal("Descriptions", profile.descriptions),
    characterSignal("Appearance", profile.appearance),
    characterSignal("Relationships", profile.relationships),
  ];
  return (
    <dl className="character-identity-strip" aria-label="Character identity signals">
      {signals.map((signal) => (
        <div key={signal.label} className={signal.count > 0 ? "" : "is-unknown"}>
          <dt>{signal.label}</dt>
          <dd>{signal.value}</dd>
        </div>
      ))}
    </dl>
  );
}

function characterSignal(
  label: string,
  section: OutputSection,
): { label: string; value: string; count: number } {
  const knownItems = knownSectionItems(section);
  const count = knownItems.length;
  const labelText = count === 1 ? "signal" : "signals";
  return {
    label,
    value: count > 0 ? `${count.toLocaleString()} ${labelText}` : "Unknown",
    count,
  };
}

function CharacterAtAGlance({ profile }: { profile: CharacterProfile }) {
  const facts = [
    characterFact("Race", profile.race),
    characterFact("Gender", profile.gender),
    characterFact("Status", profile.status),
    characterFact("Goal", profile.current_goal),
  ];
  return (
    <dl className="character-fact-strip" aria-label="Character at a glance">
      {facts.map((fact) => (
        <div key={fact.label}>
          <dt>{fact.label}</dt>
          <dd>{fact.value}</dd>
        </div>
      ))}
    </dl>
  );
}

function characterFact(label: string, section: OutputSection): { label: string; value: string } {
  const knownItems = readableOutputItems(section.items).filter((item) => item !== "Unknown");
  return { label, value: knownItems[0] ?? "Unknown" };
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

function evidenceFactCount(summary: string): number {
  const match = summary.match(/(\d[\d,]*)\s+verified facts?/i);
  return match ? Number(match[1].replace(/,/g, "")) : 0;
}

function characterRecentChanges(profile: CharacterProfile): OutputSection {
  const representedValues = representedCharacterProfileValues(profile);
  return {
    title: profile.recent_changes.title,
    items: readableOutputItems(profile.recent_changes.items).filter(
      (item) => !isRepresentedCharacterProfileChange(item, representedValues),
    ),
  };
}

function representedCharacterProfileValues(profile: CharacterProfile): Set<string> {
  const representedSections = [
    profile.aliases,
    profile.titles,
    profile.descriptions,
    profile.appearance,
    profile.race,
    profile.gender,
    profile.status,
    profile.current_goal,
    profile.current_equipment,
    profile.current_abilities,
    profile.current_assets,
    profile.territory,
    profile.relationships,
    profile.current_limitations,
    profile.first_appearance,
    profile.latest_appearance,
    profile.timeline_history,
    profile.evidence_references,
  ];
  return new Set(
    [
      readableCharacterName(profile.display_name),
      readableCharacterSubtitle(profile.subtitle),
      ...representedSections.flatMap((section) => readableOutputItems(section.items)),
    ]
      .flatMap((item) => [item, profileChangeValue(item)])
      .map(normalizedProfileComparisonValue)
      .filter(Boolean),
  );
}

function isRepresentedCharacterProfileChange(
  item: string,
  representedValues: Set<string>,
): boolean {
  const label = normalizedProfileComparisonValue(profileChangeLabel(item));
  const normalizedItem = normalizedProfileComparisonValue(item);
  const normalizedValue = normalizedProfileComparisonValue(profileChangeValue(item));
  return (
    CHARACTER_RECENT_CHANGE_PROFILE_LABELS.has(label) ||
    representedValues.has(normalizedItem) ||
    representedValues.has(normalizedValue)
  );
}

function profileChangeLabel(item: string): string {
  const labelMatch = item.match(/^([^:]+):\s*.+$/u);
  return labelMatch ? labelMatch[1] : "";
}

function profileChangeValue(item: string): string {
  const valueMatch = item.match(/^[^:]+:\s*(.+)$/u);
  return valueMatch ? valueMatch[1] : item;
}

function normalizedProfileComparisonValue(value: string): string {
  return value.trim().toLowerCase();
}

function readableCharacterSubtitle(subtitle: string): string {
  if (!subtitle || subtitle === "Unknown" || isInternalOutputPlaceholder(subtitle)) {
    return "Unknown";
  }
  return readableOutputText(subtitle);
}

function readableCharacterName(name: string): string {
  if (!name || name === "Unknown" || isInternalOutputPlaceholder(name)) {
    return "Unknown character";
  }
  return readableOutputText(name);
}

function CharacterPanels({
  profiles,
  projectId,
  sessionToken,
}: {
  profiles: CharacterProfile[];
  projectId: string;
  sessionToken: string;
}) {
  const [query, setQuery] = useState("");
  const [visibleCount, setVisibleCount] = useState(CHARACTER_CARD_PAGE_SIZE);
  const normalizedQuery = query.trim().toLowerCase();
  const filteredProfiles = normalizedQuery
    ? profiles.filter((profile) =>
        searchableCharacterText(profile).toLowerCase().includes(normalizedQuery),
      )
    : profiles;
  const visibleProfiles = filteredProfiles.slice(0, visibleCount);
  const hiddenCount = Math.max(filteredProfiles.length - visibleProfiles.length, 0);

  function updateQuery(value: string) {
    setQuery(value);
    setVisibleCount(CHARACTER_CARD_PAGE_SIZE);
  }

  return (
    <div className="large-output-stack">
      <div className="large-output-controls">
        <label>
          Search characters
          <input
            value={query}
            onChange={(event) => updateQuery(event.target.value)}
            placeholder="Name, title, role, evidence"
          />
        </label>
        <p>
          Showing {visibleProfiles.length.toLocaleString()} of{" "}
          {filteredProfiles.length.toLocaleString()} character profiles.
        </p>
      </div>
      {visibleProfiles.length > 0 ? (
        <div className="profile-grid character-card-grid" aria-label="Character cards">
          {visibleProfiles.map((profile) => (
            <CharacterPanel
              key={profile.character_id}
              profile={profile}
              projectId={projectId}
              sessionToken={sessionToken}
            />
          ))}
        </div>
      ) : (
        <EmptyState title="No matching characters">
          No character profiles match the current search.
        </EmptyState>
      )}
      <LoadMoreButton
        hiddenCount={hiddenCount}
        pageSize={CHARACTER_CARD_PAGE_SIZE}
        onLoadMore={() =>
          setVisibleCount((currentCount) => currentCount + CHARACTER_CARD_PAGE_SIZE)
        }
      />
    </div>
  );
}

function searchableCharacterText(profile: CharacterProfile): string {
  const sections = [
    profile.aliases,
    profile.titles,
    profile.descriptions,
    profile.race,
    profile.gender,
    profile.status,
    profile.current_goal,
    profile.current_equipment,
    profile.current_abilities,
    profile.current_assets,
    profile.territory,
    profile.relationships,
    profile.current_limitations,
    characterRecentChanges(profile),
  ];
  return [
    readableCharacterName(profile.display_name),
    readableCharacterSubtitle(profile.subtitle),
    profile.evidence_summary,
    ...sections.flatMap((section) => readableOutputItems(section.items)),
  ].join(" ");
}

function WorldPanel({
  world,
  projectId,
  sessionToken,
}: {
  world: WorldSheet;
  projectId: string;
  sessionToken: string;
}) {
  const [query, setQuery] = useState("");
  const [visibleCount, setVisibleCount] = useState(WORLD_CARD_PAGE_SIZE);
  const normalizedQuery = query.trim().toLowerCase();
  const filteredSections = normalizedQuery
    ? world.entity_sections.filter((section) =>
        searchableWorldSectionText(section).toLowerCase().includes(normalizedQuery),
      )
    : world.entity_sections;
  const visibleSections = filteredSections.slice(0, visibleCount);
  const hiddenCount = Math.max(filteredSections.length - visibleSections.length, 0);

  function updateQuery(value: string) {
    setQuery(value);
    setVisibleCount(WORLD_CARD_PAGE_SIZE);
  }

  return (
    <div className="large-output-stack">
      <div className="large-output-controls">
        <label>
          Search world
          <input
            value={query}
            onChange={(event) => updateQuery(event.target.value)}
            placeholder="Name, type, ownership, condition"
          />
        </label>
        <p>
          Showing {visibleSections.length.toLocaleString()} of{" "}
          {filteredSections.length.toLocaleString()} world sections.
        </p>
      </div>
      <LimitedResultsNote
        shown={visibleSections.length}
        total={filteredSections.length}
        label="world sections"
      />
      {visibleSections.length > 0 ? (
        <div className="profile-grid" aria-label="World sheets">
          {visibleSections.map((section) => (
            <article className="profile-card" key={section.title}>
              <header>
                <h3>{section.title}</h3>
              </header>
              <details className="profile-disclosure">
                <summary>World details</summary>
                <WorldSection section={section} />
              </details>
              <CorrectionEditor
                correctionKind="world"
                fieldOptions={WORLD_CORRECTION_FIELDS}
                projectId={projectId}
                sessionToken={sessionToken}
                targetId={`world_${machineToken(section.title)}`}
                targetLabel={section.title}
              />
            </article>
          ))}
        </div>
      ) : (
        <EmptyState title="No matching world entries">
          No world sections match the current search.
        </EmptyState>
      )}
      <LoadMoreButton
        hiddenCount={hiddenCount}
        pageSize={WORLD_CARD_PAGE_SIZE}
        onLoadMore={() => setVisibleCount((currentCount) => currentCount + WORLD_CARD_PAGE_SIZE)}
      />
      <p className="evidence-note">{world.evidence_summary}</p>
    </div>
  );
}

function searchableWorldSectionText(section: OutputSection): string {
  return [section.title, ...readableOutputItems(section.items)].join(" ");
}

function TimelinePanel({ changes }: { changes: ProjectTimelineChange[] }) {
  const [visibleCount, setVisibleCount] = useState(TIMELINE_GROUP_PAGE_SIZE);
  const timelineGroups = groupedTimelineChanges(changes);
  const visibleGroups = timelineGroups.slice(0, visibleCount);
  const hiddenCount = Math.max(timelineGroups.length - visibleGroups.length, 0);
  return (
    <div className="compact-list timeline-change-list" aria-label="Timeline changes">
      <LimitedResultsNote
        shown={visibleGroups.length}
        total={timelineGroups.length}
        label="timeline groups"
      />
      {visibleGroups.map((group) => (
        <details
          className="compact-row timeline-change-group detail-disclosure"
          key={`${group.chapterIndex}-${group.sceneIndex}`}
          aria-label={`${group.title} timeline details`}
        >
          <summary>
            <strong>{group.title}</strong>
            <span aria-hidden="true"> - </span>
            <span>
              {group.subtitle}; {timelineGroupChangeLabel(group.changes.length)}
            </span>
          </summary>
          <ul>
            {group.changes.map((change) => (
              <li key={change.change_id}>
                <strong>{change.entity_name}</strong>
                <span aria-hidden="true"> - </span>
                <span>
                  {readableLabel(change.attribute)}: {change.value}
                </span>
              </li>
            ))}
          </ul>
        </details>
      ))}
      <LoadMoreButton
        hiddenCount={hiddenCount}
        pageSize={TIMELINE_GROUP_PAGE_SIZE}
        onLoadMore={() =>
          setVisibleCount((currentCount) => currentCount + TIMELINE_GROUP_PAGE_SIZE)
        }
      />
    </div>
  );
}

function SceneSheetsPanel({ scenes }: { scenes: SceneSheet[] }) {
  const [visibleCount, setVisibleCount] = useState(SCENE_CARD_PAGE_SIZE);
  const visibleScenes = scenes.slice(0, visibleCount);
  const hiddenCount = Math.max(scenes.length - visibleScenes.length, 0);
  return (
    <div className="large-output-stack">
      <LimitedResultsNote shown={visibleScenes.length} total={scenes.length} label="scene sheets" />
      <div className="profile-grid" aria-label="Scene sheets">
        {visibleScenes.map((scene) => (
          <article className="profile-card" key={scene.scene_id}>
            <header>
              <h3>{scene.title}</h3>
              <p>{scene.chapter_label}</p>
            </header>
            <details className="profile-disclosure">
              <summary>Scene details</summary>
              <div className="profile-section-grid">
                <PanelSection section={scene.characters_present} />
                <PanelSection section={scene.location} />
                <PanelSection section={scene.mood} />
                <PanelSection section={scene.purpose} />
                <PanelSection section={scene.visual_highlights} />
                <PanelSection section={scene.continuity_changes} />
                <PanelSection section={scene.environment} />
              </div>
            </details>
            <p className="evidence-note">{scene.evidence_summary}</p>
          </article>
        ))}
      </div>
      <LoadMoreButton
        hiddenCount={hiddenCount}
        pageSize={SCENE_CARD_PAGE_SIZE}
        onLoadMore={() => setVisibleCount((currentCount) => currentCount + SCENE_CARD_PAGE_SIZE)}
      />
    </div>
  );
}

function ContinuityPanel({ report }: { report: ContinuityReport }) {
  const [visibleCount, setVisibleCount] = useState(CONTINUITY_SCENE_PAGE_SIZE);
  const scenesWithChanges = report.scenes.filter(
    (scene) =>
      scene.new.length > 0 ||
      scene.updated.length > 0 ||
      scene.still_known.length > 0 ||
      scene.invalidated.length > 0,
  );
  const visibleScenes = scenesWithChanges.slice(0, visibleCount);
  const hiddenCount = Math.max(scenesWithChanges.length - visibleScenes.length, 0);
  if (visibleScenes.length === 0) {
    return (
      <EmptyState title="No continuity changes">
        Aevryn did not find continuity changes in the latest processed snapshot.
      </EmptyState>
    );
  }
  return (
    <div className="compact-list timeline-change-list" aria-label="Continuity report">
      <LimitedResultsNote
        shown={visibleScenes.length}
        total={scenesWithChanges.length}
        label="continuity scenes"
      />
      {visibleScenes.map((scene) => (
        <details
          className="compact-row timeline-change-group detail-disclosure"
          key={scene.scene_id}
          aria-label={`${formatSceneScope(scene.scene_id)} continuity details`}
        >
          <summary>
            <strong>{formatSceneScope(scene.scene_id)}</strong>
            <span aria-hidden="true"> - </span>
            <span>{continuitySceneSummary(scene)}</span>
          </summary>
          <ContinuityScenePreview scene={scene} />
          <div className="continuity-change-grid">
            <ContinuityBucket title="New Canon" records={scene.new} />
            <ContinuityBucket title="Changed Canon" records={scene.updated} />
            <ContinuityBucket title="No Longer Current" records={scene.invalidated} />
          </div>
          {scene.still_known.length > 0 ? (
            <details className="nested-disclosure">
              <summary>{`${scene.still_known.length.toLocaleString()} retained canon`}</summary>
              <ContinuityBucket title="Retained Canon" records={scene.still_known} />
            </details>
          ) : null}
        </details>
      ))}
      <LoadMoreButton
        hiddenCount={hiddenCount}
        pageSize={CONTINUITY_SCENE_PAGE_SIZE}
        onLoadMore={() =>
          setVisibleCount((currentCount) => currentCount + CONTINUITY_SCENE_PAGE_SIZE)
        }
      />
    </div>
  );
}

function ContinuityScenePreview({ scene }: { scene: ContinuityReport["scenes"][number] }) {
  const previewItems = continuityPreviewItems(scene);
  if (previewItems.length === 0) {
    return null;
  }
  return (
    <ul className="continuity-preview-list" aria-label="Continuity highlights">
      {previewItems.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  );
}

function ContinuityBucket({
  title,
  records,
}: {
  title: string;
  records: ContinuityReport["scenes"][number]["new"];
}) {
  if (records.length === 0) {
    return null;
  }
  const readableRecords = records
    .map((record) => ({
      record,
      description: readableOutputItems([record.description])[0] ?? "",
    }))
    .filter(({ description }) => description && description !== "Unknown");
  if (readableRecords.length === 0) {
    return null;
  }
  const visibleRecords = readableRecords.slice(0, 8);
  const hiddenCount = readableRecords.length - visibleRecords.length;
  return (
    <div>
      <strong>{title}</strong>
      <ul>
        {visibleRecords.map(({ record, description }) => (
          <li key={record.record_id}>
            <span>{description}</span>
          </li>
        ))}
      </ul>
      {hiddenCount > 0 ? (
        <p className="field-note">
          {hiddenCount.toLocaleString()} additional {title.toLowerCase()} records hidden.
        </p>
      ) : null}
    </div>
  );
}

function PromptPacksPanel({ packs }: { packs: ProductionPack[] }) {
  const [query, setQuery] = useState("");
  const [visibleCount, setVisibleCount] = useState(MAX_VISIBLE_PROMPT_SCENES);
  const normalizedQuery = query.trim().toLowerCase();
  const filteredPacks = normalizedQuery
    ? packs.filter((pack) => searchablePromptPackText(pack).includes(normalizedQuery))
    : packs;
  const visiblePacks = filteredPacks.slice(0, visibleCount);
  const hiddenPromptSceneCount = Math.max(filteredPacks.length - visiblePacks.length, 0);
  const [selectedSceneId, setSelectedSceneId] = useState(packs[0]?.scene.scene_id ?? "");

  function updateQuery(value: string) {
    setQuery(value);
    setVisibleCount(MAX_VISIBLE_PROMPT_SCENES);
  }

  const selectedPack =
    filteredPacks.find((pack) => pack.scene.scene_id === selectedSceneId) ?? filteredPacks[0];
  if (!selectedPack) {
    return (
      <div className="prompt-pack-browser">
        <PromptSceneSearch
          query={query}
          resultCount={filteredPacks.length}
          totalCount={packs.length}
          onChange={updateQuery}
        />
        <EmptyState title="No matching prompt scenes">
          No prompt scenes match the current search.
        </EmptyState>
      </div>
    );
  }
  const selectedIndex = filteredPacks.findIndex(
    (pack) => pack.scene.scene_id === selectedPack.scene.scene_id,
  );
  const previousPack = selectedIndex > 0 ? filteredPacks[selectedIndex - 1] : null;
  const nextPack =
    selectedIndex >= 0 && selectedIndex < filteredPacks.length - 1
      ? filteredPacks[selectedIndex + 1]
      : null;

  return (
    <div className="prompt-pack-browser">
      <PromptSceneSearch
        query={query}
        resultCount={filteredPacks.length}
        totalCount={packs.length}
        onChange={updateQuery}
      />
      {filteredPacks.length > visiblePacks.length ? (
        <p className="result-summary">
          Showing {visiblePacks.length.toLocaleString()} of{" "}
          {filteredPacks.length.toLocaleString()} prompt scenes. Select a scene to view its
          production prompts, or load more scenes when needed.
        </p>
      ) : null}
      <div className="prompt-pack-layout">
        <div className="prompt-scene-picker">
          <div className="prompt-scene-list" aria-label="Prompt scenes">
            {visiblePacks.map((pack) => (
              <button
                type="button"
                className="prompt-scene-button"
                aria-label={`${pack.scene.title} ${pack.scene.chapter_label} ${pack.scene.evidence_summary}`}
                aria-pressed={pack.scene.scene_id === selectedPack.scene.scene_id}
                key={pack.scene.scene_id}
                onClick={() => setSelectedSceneId(pack.scene.scene_id)}
              >
                <strong>{pack.scene.title}</strong>
                <span>{pack.scene.chapter_label}</span>
                <small>{pack.scene.evidence_summary}</small>
              </button>
            ))}
          </div>
          {hiddenPromptSceneCount > 0 ? (
            <button
              type="button"
              className="secondary-button prompt-scene-more-button"
              onClick={() => setVisibleCount((count) => count + MAX_VISIBLE_PROMPT_SCENES)}
            >
              Show {Math.min(MAX_VISIBLE_PROMPT_SCENES, hiddenPromptSceneCount).toLocaleString()}{" "}
              more scenes
            </button>
          ) : null}
        </div>
        <article className="profile-card prompt-pack-detail" aria-label="Selected prompt pack">
          <header className="prompt-pack-header">
            <div>
              <h3>{selectedPack.scene.title}</h3>
              <p>{selectedPack.scene.chapter_label}</p>
            </div>
            <span>{selectedPack.scene.evidence_summary}</span>
          </header>
          <div className="prompt-scene-navigation" aria-label="Selected prompt scene navigation">
            <button
              type="button"
              className="text-button"
              disabled={!previousPack}
              onClick={() => {
                if (previousPack) {
                  setSelectedSceneId(previousPack.scene.scene_id);
                }
              }}
            >
              Previous scene
            </button>
            <span>
              Scene {(selectedIndex + 1).toLocaleString()} of{" "}
              {filteredPacks.length.toLocaleString()}
            </span>
            <button
              type="button"
              className="text-button"
              disabled={!nextPack}
              onClick={() => {
                if (nextPack) {
                  setSelectedSceneId(nextPack.scene.scene_id);
                }
              }}
            >
              Next scene
            </button>
          </div>
          <PromptProductionFocus pack={selectedPack} />
          <div className="prompt-pack-dossier">
            <PromptCanonInputs pack={selectedPack} />
            <PromptSceneBrief pack={selectedPack} />
          </div>
          <details className="prompt-context-disclosure detail-disclosure">
            <summary>
              <span>Canon context</span>
              <span>Characters, setting, visuals, continuity</span>
            </summary>
            <div className="profile-section-grid prompt-scene-context">
              <PanelSection section={selectedPack.scene.characters_present} />
              <PanelSection section={selectedPack.scene.location} />
              <PanelSection section={selectedPack.scene.mood} />
              <PanelSection section={selectedPack.scene.purpose} />
              <PanelSection section={selectedPack.scene.visual_highlights} />
              <PanelSection section={selectedPack.scene.environment} />
            </div>
          </details>
          <div className="prompt-pack-grid">
            <PromptTextSection section={selectedPack.image_prompt} full />
            <PromptTextSection section={selectedPack.narration_prompt} full />
            <PromptTextSection section={selectedPack.camera_prompt} full />
            <PromptTextSection section={selectedPack.animation_prompt} full />
          </div>
        </article>
      </div>
    </div>
  );
}

function PromptSceneSearch({
  query,
  resultCount,
  totalCount,
  onChange,
}: {
  query: string;
  resultCount: number;
  totalCount: number;
  onChange: (value: string) => void;
}) {
  return (
    <div className="large-output-controls prompt-scene-search">
      <label>
        Search prompt scenes
        <input
          value={query}
          onChange={(event) => onChange(event.target.value)}
          placeholder="Chapter, scene, character, setting, visual detail"
        />
      </label>
      <p>
        Showing {resultCount.toLocaleString()} of {totalCount.toLocaleString()} prompt scenes.
      </p>
    </div>
  );
}

function searchablePromptPackText(pack: ProductionPack): string {
  return [
    pack.scene.title,
    pack.scene.chapter_label,
    pack.scene.evidence_summary,
    ...readableOutputItems(pack.scene.characters_present.items),
    ...readableOutputItems(pack.scene.location.items),
    ...readableOutputItems(pack.scene.visual_highlights.items),
    ...readableOutputItems(pack.scene.environment.items),
    ...readableOutputItems(pack.scene.continuity_changes.items),
  ]
    .join(" ")
    .toLowerCase();
}

function PromptProductionFocus({ pack }: { pack: ProductionPack }) {
  const guardrailCount = promptGuardrailCount(pack);
  const missingInputs = promptMissingInputLabels(pack);
  const missingLabel =
    missingInputs.length > 0
      ? `${missingInputs.join(", ")} stay neutral`
      : "Known inputs are ready";
  return (
    <dl className="prompt-production-focus" aria-label="Prompt production focus">
      <div>
        <dt>Scene priority</dt>
        <dd>Current scene before retained Canon</dd>
      </div>
      <div>
        <dt>Generation boundary</dt>
        <dd>
          {guardrailCount.toLocaleString()} canon guardrail
          {guardrailCount === 1 ? "" : "s"}; no unsupported additions
        </dd>
      </div>
      <div>
        <dt>Missing inputs</dt>
        <dd>{missingLabel}</dd>
      </div>
    </dl>
  );
}

function PromptSceneBrief({ pack }: { pack: ProductionPack }) {
  const items = [
    promptSceneBriefItem("Characters", pack.scene.characters_present),
    promptSceneBriefItem("Setting", pack.scene.location, pack.scene.environment),
    promptSceneBriefItem("Visuals", pack.scene.visual_highlights),
    promptSceneBriefItem("Purpose", pack.scene.purpose),
  ];
  return (
    <dl className="prompt-scene-brief" aria-label="Selected prompt scene brief">
      {items.map((item) => (
        <div key={item.label}>
          <dt>{item.label}</dt>
          <dd>{item.value}</dd>
        </div>
      ))}
    </dl>
  );
}

function promptSceneBriefItem(
  label: string,
  ...sections: OutputSection[]
): { label: string; value: string } {
  const values = sections.flatMap((section) => knownSectionItems(section));
  return {
    label,
    value: values.slice(0, 2).join("; ") || "Unknown",
  };
}

function PromptCanonInputs({ pack }: { pack: ProductionPack }) {
  const guardrailCount = promptGuardrailCount(pack);
  const inputs = [
    promptInputStatus("Characters", pack.scene.characters_present),
    promptInputStatus("Setting", pack.scene.location, pack.scene.environment),
    promptInputStatus("Visual details", pack.scene.visual_highlights),
    promptInputStatus("Continuity", pack.scene.continuity_changes),
    {
      label: "Constraints",
      status: guardrailCount > 0 ? "available" : "missing",
      statusLabel: guardrailCount > 0 ? "Available" : "Missing",
      detail:
        guardrailCount > 0
          ? `${guardrailCount.toLocaleString()} canon guardrail${
              guardrailCount === 1 ? "" : "s"
            }`
          : "No explicit guardrails",
    },
  ];
  return (
    <div className="prompt-canon-inputs" aria-label="Prompt canon inputs">
      <strong>Canon inputs</strong>
      <dl>
        {inputs.map((input) => (
          <div
            className={`prompt-canon-input prompt-canon-input-${input.status}`}
            key={input.label}
          >
            <dt>{input.label}</dt>
            <dd>
              <span>{input.statusLabel}</span>
              <small>{input.detail}</small>
            </dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

function promptMissingInputLabels(pack: ProductionPack): string[] {
  return [
    promptInputStatus("Characters", pack.scene.characters_present),
    promptInputStatus("Setting", pack.scene.location, pack.scene.environment),
    promptInputStatus("Visual details", pack.scene.visual_highlights),
    promptInputStatus("Continuity", pack.scene.continuity_changes),
  ]
    .filter((input) => input.status === "missing")
    .map((input) => input.label.toLowerCase());
}

function promptInputStatus(
  label: string,
  ...sections: OutputSection[]
): {
  label: string;
  status: "available" | "missing";
  statusLabel: string;
  detail: string;
} {
  const values = sections.flatMap((section) => knownSectionItems(section));
  const count = values.length;
  const preview = values.slice(0, 2).join("; ");
  return {
    label,
    status: count > 0 ? "available" : "missing",
    statusLabel: count > 0 ? "Available" : "Missing",
    detail:
      count > 0
        ? `${count.toLocaleString()} known detail${count === 1 ? "" : "s"}${
            preview ? `: ${preview}` : ""
          }`
        : "No accepted details yet",
  };
}

function knownSectionItems(section: OutputSection): string[] {
  return readableOutputItems(section.items).filter((item) => item !== "Unknown");
}

function promptGuardrailCount(pack: ProductionPack): number {
  const guardrailPatterns = [
    /\bonly accepted\b/iu,
    /\bwithout inventing\b/iu,
    /\bunsupported\b/iu,
    /\bforbidden\b/iu,
    /\bdo not\b/iu,
    /\bmust not\b/iu,
  ];
  return readableOutputItems([
    ...pack.image_prompt.items,
    ...pack.narration_prompt.items,
    ...pack.camera_prompt.items,
    ...pack.animation_prompt.items,
  ]).filter((item) => guardrailPatterns.some((pattern) => pattern.test(item))).length;
}

function continuitySceneSummary(scene: ContinuityReport["scenes"][number]): string {
  const changeCount = continuityChangeCount(scene);
  const stableCount = scene.still_known.length;
  const changeLabel = `${changeCount.toLocaleString()} change${changeCount === 1 ? "" : "s"}`;
  const stableLabel = `${stableCount.toLocaleString()} retained canon`;
  const firstChange = continuityPreviewItems(scene)[0];
  if (!firstChange) {
    return `${changeLabel}; ${stableLabel}`;
  }
  return `${changeLabel}: ${firstChange}; ${stableLabel}`;
}

function continuityPreviewItems(scene: ContinuityReport["scenes"][number]): string[] {
  const records = [
    ...scene.new.map((record) => ({ ...record, bucket: "New canon" })),
    ...scene.updated.map((record) => ({ ...record, bucket: "Changed canon" })),
    ...scene.invalidated.map((record) => ({ ...record, bucket: "No longer current" })),
  ];
  return records.slice(0, 2).map((record) => {
    const description = readableOutputItems([record.description])[0] ?? "Unknown";
    return `${record.bucket}: ${description}`;
  });
}

function timelineGroupChangeLabel(changeCount: number): string {
  return `${changeCount.toLocaleString()} change${changeCount === 1 ? "" : "s"}`;
}

function continuityChangeCount(scene: ContinuityReport["scenes"][number]): number {
  return scene.new.length + scene.updated.length + scene.invalidated.length;
}

function ExportOptionsPanel({ options }: { options: ProjectExportOption[] }) {
  return (
    <div className="compact-list" aria-label="Export options">
      {options.map((option) => (
        <div className="compact-row" key={option.export_kind}>
          <strong>{option.label}</strong>
          <span>{option.formats.map((format) => format.toUpperCase()).join(", ")}</span>
        </div>
      ))}
    </div>
  );
}

function groupedTimelineChanges(changes: ProjectTimelineChange[]): Array<{
  chapterIndex: number;
  sceneIndex: number;
  title: string;
  subtitle: string;
  changes: ProjectTimelineChange[];
}> {
  const groups = new Map<
    string,
    {
      chapterIndex: number;
      sceneIndex: number;
      title: string;
      subtitle: string;
      changes: ProjectTimelineChange[];
    }
  >();
  for (const change of changes) {
    const key = `${change.chapter_index}:${change.scene_index}`;
    const existingGroup = groups.get(key);
    if (existingGroup) {
      existingGroup.changes.push(change);
      continue;
    }
    groups.set(key, {
      chapterIndex: change.chapter_index,
      sceneIndex: change.scene_index,
      title: `Chapter ${change.chapter_index}, Scene ${change.scene_index}`,
      subtitle: sceneTitle(change),
      changes: [change],
    });
  }
  return Array.from(groups.values());
}

function sceneTitle(change: ProjectTimelineChange): string {
  const chapterTitle = change.chapter_title || `Chapter ${change.chapter_index}`;
  const sceneTitle = change.scene_title || `Scene ${change.scene_index}`;
  if (chapterTitle === sceneTitle) {
    return chapterTitle;
  }
  return `${chapterTitle} / ${sceneTitle}`;
}

type CorrectionKind = "character" | "world";
type CorrectionFieldOption = { readonly field: string; readonly label: string };

function CorrectionEditor({
  correctionKind,
  fieldOptions,
  projectId,
  sessionToken,
  targetId,
  targetLabel,
}: {
  correctionKind: CorrectionKind;
  fieldOptions: readonly CorrectionFieldOption[];
  projectId: string;
  sessionToken: string;
  targetId: string;
  targetLabel: string;
}) {
  const queryClient = useQueryClient();
  const [fieldName, setFieldName] = useState(fieldOptions[0]?.field ?? "");
  const [isOpen, setIsOpen] = useState(false);
  const [value, setValue] = useState("");
  const [savedLabel, setSavedLabel] = useState("");
  const saveCorrection = useMutation({
    mutationFn: (payload: ProjectCorrectionRequest & { correctionId: string }) => {
      const now = nowUtc();
      return apiClient.upsertProjectCorrection(
        projectId,
        payload.correctionId,
        {
          target_type: payload.target_type,
          target_id: payload.target_id,
          field_name: payload.field_name,
          value: payload.value,
          now,
        },
        sessionToken,
        now,
      );
    },
    async onSuccess(result) {
      setSavedLabel(`${readableLabel(result.field_name)} saved as User Edited.`);
      setValue("");
      await queryClient.invalidateQueries({
        queryKey: projectOutputsQueryKey(projectId, sessionToken),
      });
    },
  });
  const trimmedValue = value.trim();
  const canSave = Boolean(sessionToken && fieldName && trimmedValue);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSave) {
      return;
    }
    setSavedLabel("");
    saveCorrection.mutate({
      correctionId: correctionId(correctionKind, targetId, fieldName),
      target_type: correctionKind,
      target_id: targetId,
      field_name: fieldName,
      value: trimmedValue,
      now: nowUtc(),
    });
  }

  return (
    <details
      className="correction-editor"
      onToggle={(event) => setIsOpen(event.currentTarget.open)}
    >
      <summary>User Edited correction</summary>
      {isOpen ? (
        <form onSubmit={submit}>
          <label>
            Field
            <select value={fieldName} onChange={(event) => setFieldName(event.target.value)}>
              {fieldOptions.map((option) => (
                <option key={option.field} value={option.field}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            Correction
            <input
              value={value}
              onChange={(event) => setValue(event.target.value)}
              placeholder={`Correct ${targetLabel}`}
            />
          </label>
          {saveCorrection.error ? (
            <ErrorMessage>{saveCorrection.error.message}</ErrorMessage>
          ) : null}
          {savedLabel ? <p className="form-success">{savedLabel}</p> : null}
          <button
            type="submit"
            className="text-button"
            disabled={!canSave || saveCorrection.isPending}
          >
            {saveCorrection.isPending ? "Saving" : "Save correction"}
          </button>
        </form>
      ) : null}
    </details>
  );
}

function correctionId(kind: CorrectionKind, targetId: string, fieldName: string): string {
  return `correction_${kind}_${machineToken(targetId)}_${machineToken(fieldName)}`;
}

function machineToken(value: string): string {
  const token = value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/gu, "_")
    .replace(/^_+|_+$/gu, "");
  return token || "unknown";
}

function PanelSection({ section }: { section: OutputSection }) {
  const items = readableOutputItems(section.items);
  return (
    <section className="profile-section">
      <h4>{section.title}</h4>
      <ul>
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}

function LimitedResultsNote({
  shown,
  total,
  label,
}: {
  shown: number;
  total: number;
  label: string;
}) {
  if (total <= shown) {
    return null;
  }
  return (
    <p className="result-summary">
      Showing {shown.toLocaleString()} of {total.toLocaleString()} {label}.
    </p>
  );
}

function LoadMoreButton({
  hiddenCount,
  pageSize,
  onLoadMore,
}: {
  hiddenCount: number;
  pageSize: number;
  onLoadMore: () => void;
}) {
  if (hiddenCount <= 0) {
    return null;
  }
  return (
    <button type="button" className="text-button" onClick={onLoadMore}>
      Show {Math.min(hiddenCount, pageSize).toLocaleString()} more
    </button>
  );
}

function PromptTextSection({ section, full = false }: { section: OutputSection; full?: boolean }) {
  const [copyState, setCopyState] = useState<"idle" | "copied" | "failed">("idle");
  const promptText = readablePromptText(
    section,
    full ? {} : { maxItems: MAX_VISIBLE_PROMPT_DETAILS },
  );
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
          <button
            type="button"
            className="text-button"
            aria-label={`Download ${section.title}`}
            onClick={() => downloadPromptText(section, promptText)}
          >
            Download
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

function WorldSection({ section }: { section: OutputSection }) {
  const items = readableOutputItems(section.items);
  return (
    <ul className="world-item-list">
      {items.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  );
}

function readableLabel(value: string): string {
  return value
    .split("_")
    .filter(Boolean)
    .map((word) => `${word.charAt(0).toUpperCase()}${word.slice(1)}`)
    .join(" ");
}

function SurfaceDetails({
  surface,
  outputs,
  surfaceSummary,
}: {
  surface: OutputSurface;
  outputs: ProjectOutputs;
  surfaceSummary: ProjectOutputSurface;
}) {
  const details = detailItems(surface, outputs);
  return (
    <div className="compact-list" aria-label={`${surfaceSummary.title} details`}>
      {details.map((item) => (
        <div className="compact-row" key={item.label}>
          <strong>{item.label}</strong>
          <span>{item.value}</span>
        </div>
      ))}
    </div>
  );
}

function detailItems(
  surface: OutputSurface,
  outputs: ProjectOutputs,
): Array<{ label: string; value: string }> {
  const canon = outputs.canon;
  const common = [
    { label: "Chapter spread", value: chapterSpreadLabel(canon.chapter_scene_counts) },
    { label: "Accepted facts", value: canon.accepted_fact_count.toLocaleString() },
    {
      label: "State changes",
      value: canon.accepted_state_change_count.toLocaleString(),
    },
  ];
  if (surface === "characters") {
    return [
      { label: "Accepted entities", value: canon.accepted_entity_count.toLocaleString() },
      ...common,
    ];
  }
  if (surface === "world") {
    return [
      {
        label: "Relationships",
        value: canon.accepted_relationship_count.toLocaleString(),
      },
      ...common,
    ];
  }
  if (surface === "scenes" || surface === "prompts" || surface === "exports") {
    return [
      { label: "Processed scenes", value: canon.scenes.toLocaleString() },
      { label: "Extraction results", value: canon.extraction_result_count.toLocaleString() },
      ...common,
    ];
  }
  return common;
}

function chapterSpreadLabel(counts: ProjectOutputs["canon"]["chapter_scene_counts"]): string {
  if (counts.length === 0) {
    return "No chapter scene metadata";
  }
  const visibleCounts = counts.slice(0, 6);
  const label = visibleCounts
    .map((item) => `Chapter ${item.chapter_index}: ${sceneCountLabel(item.scene_count)}`)
    .join("; ");
  return counts.length > visibleCounts.length ? `${label}; ...` : label;
}

function sceneCountLabel(count: number): string {
  return count === 1 ? "1 scene" : `${count.toLocaleString()} scenes`;
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

function projectOutputsQueryKey(projectId: string, sessionToken: string | undefined) {
  return ["project-outputs", projectId, sessionToken] as const;
}

function nowUtc(): string {
  return new Date().toISOString();
}

function requireSessionToken(session: { session_token: string } | null): string {
  if (!session) {
    throw new Error("Aevryn session is required.");
  }
  return session.session_token;
}
