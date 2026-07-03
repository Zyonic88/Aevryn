import { useQuery } from "@tanstack/react-query";
import type { ReactNode } from "react";

import { apiClient } from "../api/client";
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
import { EmptyState, LoadingMessage } from "../components/Feedback";
import { formatDateTime, formatRunStatus } from "../formatting/display";
import type { ProjectSummary } from "../projects/projectStore";
import {
  compactIdentityReviewItems,
  identityReviewDetails,
  identityReviewKey,
  identityReviewStatusLabel,
  reviewItemCountLabel,
  translationReviewDetails,
  translationReviewKey,
} from "./languageIdentityDisplay";
import { readableOutputItems, readablePromptText } from "./readableOutput";

type OutputSurface =
  "characters" | "world" | "timeline" | "scenes" | "continuity" | "prompts" | "exports";

const MAX_VISIBLE_PROMPT_PACKS = 6;
const MAX_VISIBLE_PROMPT_DETAILS = 10;

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
  return <ProjectOutputSummary outputs={outputsQuery.data} surface={surface} />;
}

export function DeveloperPreviewToggle({ children }: { children: ReactNode }) {
  return (
    <details className="project-panel">
      <summary>Developer preview</summary>
      <div className="workspace-view-stack developer-preview-stack">{children}</div>
    </details>
  );
}

function ProjectOutputSummary({
  outputs,
  surface,
}: {
  outputs: ProjectOutputs;
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

  return (
    <section className="project-panel" aria-label="Processed project output">
      <h2>{surfaceSummary.title}</h2>
      <p className="result-summary">{surfaceSummary.summary}</p>
      <dl className="metric-grid">
        <Metric label="State" value={formatRunStatus(surfaceSummary.status)} />
        <Metric label="Items" value={surfaceSummary.item_count.toLocaleString()} />
        <Metric label="Import" value={outputs.latest_import ? "Latest import" : "No import"} />
        <Metric
          label="Run"
          value={
            outputs.latest_engine_run ? formatRunStatus(outputs.latest_engine_run.status) : "No run"
          }
        />
        <Metric label="Chapters" value={outputs.canon.chapters.toLocaleString()} />
        <Metric label="Scenes" value={outputs.canon.scenes.toLocaleString()} />
        <Metric label="Evidence" value={outputs.canon.evidence_anchor_count.toLocaleString()} />
        <Metric label="Snapshot" value={formatDateTime(outputs.canon.created_at)} />
      </dl>
      <LanguageIdentityStatus outputs={outputs} />
      <SurfaceDetails surface={surface} outputs={outputs} surfaceSummary={surfaceSummary} />
      <ReadableSurfacePanels surface={surface} outputs={outputs} />
      {surfaceSummary.status === "waiting" ? (
        <EmptyState title="No extracted canon content yet">
          This project has imported chapter and scene structure, but this output needs accepted
          extraction data before it can show creator-facing content.
        </EmptyState>
      ) : null}
    </section>
  );
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
      {summary.translation_review_items.slice(0, 4).map((item) => (
        <div className="compact-row" key={translationReviewKey(item)}>
          <strong>{item.issue_label}</strong>
          <span>{translationReviewDetails(item)}</span>
        </div>
      ))}
      {compactIdentityReviewItems(summary.identity_review_items, 4).map((item) => (
        <div className="compact-row" key={identityReviewKey(item)}>
          <strong>{identityReviewStatusLabel(item.status)}</strong>
          <span>{identityReviewDetails(item, identityReviewAction(item.status))}</span>
        </div>
      ))}
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

function ReadableSurfacePanels({
  surface,
  outputs,
}: {
  surface: OutputSurface;
  outputs: ProjectOutputs;
}) {
  if (surface === "characters" && outputs.character_profiles.length > 0) {
    const characterProfiles = mergeCharacterProfiles(outputs.character_profiles);
    return (
      <div className="profile-grid" aria-label="Character cards">
        {characterProfiles.map((profile) => (
          <CharacterPanel key={profile.character_id} profile={profile} />
        ))}
      </div>
    );
  }
  if (
    surface === "world" &&
    outputs.world_sheet &&
    outputs.world_sheet.entity_sections.length > 0
  ) {
    return <WorldPanel world={outputs.world_sheet} />;
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
  if (left && left !== "Unknown") {
    return left;
  }
  return right || left;
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

function CharacterPanel({ profile }: { profile: CharacterProfile }) {
  const recentChanges = characterRecentChanges(profile);
  return (
    <article className="profile-card">
      <header>
        <h3>{profile.display_name}</h3>
        <p>{profile.subtitle}</p>
      </header>
      <div className="profile-section-grid">
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
        <PanelSection section={recentChanges} />
      </div>
      <p className="evidence-note">{profile.evidence_summary}</p>
    </article>
  );
}

function evidenceFactCount(summary: string): number {
  const match = summary.match(/(\d[\d,]*)\s+verified facts?/i);
  return match ? Number(match[1].replace(/,/g, "")) : 0;
}

function characterRecentChanges(profile: CharacterProfile): OutputSection {
  return {
    title: profile.recent_changes.title,
    items: readableOutputItems(profile.recent_changes.items).filter(
      (item) =>
        !item.startsWith("Name: ") && !item.startsWith("Race: ") && !item.startsWith("Gender: "),
    ),
  };
}

function WorldPanel({ world }: { world: WorldSheet }) {
  return (
    <div>
      <div className="profile-grid" aria-label="World sheets">
        {world.entity_sections.map((section) => (
          <article className="profile-card" key={section.title}>
            <header>
              <h3>{section.title}</h3>
            </header>
            <WorldSection section={section} />
          </article>
        ))}
      </div>
      <p className="evidence-note">{world.evidence_summary}</p>
    </div>
  );
}

function TimelinePanel({ changes }: { changes: ProjectTimelineChange[] }) {
  const timelineGroups = groupedTimelineChanges(changes);
  return (
    <div className="compact-list timeline-change-list" aria-label="Timeline changes">
      {timelineGroups.map((group) => (
        <section
          className="compact-row timeline-change-group"
          key={`${group.chapterIndex}-${group.sceneIndex}`}
        >
          <div>
            <strong>{group.title}</strong>
            <span>{group.subtitle}</span>
          </div>
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
        </section>
      ))}
    </div>
  );
}

function SceneSheetsPanel({ scenes }: { scenes: SceneSheet[] }) {
  return (
    <div className="profile-grid" aria-label="Scene sheets">
      {scenes.map((scene) => (
        <article className="profile-card" key={scene.scene_id}>
          <header>
            <h3>{scene.title}</h3>
            <p>{scene.chapter_label}</p>
          </header>
          <div className="profile-section-grid">
            <PanelSection section={scene.characters_present} />
            <PanelSection section={scene.location} />
            <PanelSection section={scene.mood} />
            <PanelSection section={scene.purpose} />
            <PanelSection section={scene.visual_highlights} />
            <PanelSection section={scene.continuity_changes} />
            <PanelSection section={scene.environment} />
          </div>
          <p className="evidence-note">{scene.evidence_summary}</p>
        </article>
      ))}
    </div>
  );
}

function ContinuityPanel({ report }: { report: ContinuityReport }) {
  const visibleScenes = report.scenes
    .filter(
      (scene) =>
        scene.new.length > 0 ||
        scene.updated.length > 0 ||
        scene.still_known.length > 0 ||
        scene.invalidated.length > 0,
    )
    .slice(0, 12);
  if (visibleScenes.length === 0) {
    return (
      <EmptyState title="No continuity changes">
        Aevryn did not find continuity changes in the latest processed snapshot.
      </EmptyState>
    );
  }
  return (
    <div className="compact-list timeline-change-list" aria-label="Continuity report">
      {visibleScenes.map((scene, index) => (
        <section className="compact-row timeline-change-group" key={scene.scene_id}>
          <div>
            <strong>{`Scene ${index + 1}`}</strong>
            <span>{continuitySceneSummary(scene)}</span>
          </div>
          <ContinuityBucket title="New" records={scene.new} />
          <ContinuityBucket title="Updated" records={scene.updated} />
          <ContinuityBucket title="Still Known" records={scene.still_known} />
          <ContinuityBucket title="Invalidated" records={scene.invalidated} />
        </section>
      ))}
    </div>
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
  return (
    <div>
      <strong>{title}</strong>
      <ul>
        {records.slice(0, 8).map((record) => (
          <li key={record.record_id}>
            <span>{readableOutputItems([record.description])[0] ?? "Unknown"}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function PromptPacksPanel({ packs }: { packs: ProductionPack[] }) {
  const visiblePacks = packs.slice(0, MAX_VISIBLE_PROMPT_PACKS);
  return (
    <>
      {packs.length > visiblePacks.length ? (
        <p className="result-summary">
          Showing {visiblePacks.length.toLocaleString()} of {packs.length.toLocaleString()} prompt
          packs.
        </p>
      ) : null}
      <div className="profile-grid" aria-label="Prompt packs">
        {visiblePacks.map((pack) => (
          <article className="profile-card" key={pack.scene.scene_id}>
            <header>
              <h3>{pack.scene.title}</h3>
              <p>{pack.scene.chapter_label}</p>
            </header>
            <div className="profile-section-grid">
              <PromptTextSection section={pack.image_prompt} />
              <PromptTextSection section={pack.narration_prompt} />
              <PromptTextSection section={pack.camera_prompt} />
              <PromptTextSection section={pack.animation_prompt} />
            </div>
            <p className="evidence-note">{pack.scene.evidence_summary}</p>
          </article>
        ))}
      </div>
    </>
  );
}

function continuitySceneSummary(scene: ContinuityReport["scenes"][number]): string {
  const changeCount = scene.new.length + scene.updated.length + scene.invalidated.length;
  const stableCount = scene.still_known.length;
  const changeLabel = `${changeCount.toLocaleString()} change${changeCount === 1 ? "" : "s"}`;
  const stableLabel = `${stableCount.toLocaleString()} still known`;
  return `${changeLabel}; ${stableLabel}`;
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

function PromptTextSection({ section }: { section: OutputSection }) {
  return (
    <section className="profile-section prompt-text-section">
      <h4>{section.title}</h4>
      <p>{readablePromptText(section, { maxItems: MAX_VISIBLE_PROMPT_DETAILS })}</p>
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
