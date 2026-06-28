import { useQuery } from "@tanstack/react-query";
import type { ReactNode } from "react";

import { apiClient } from "../api/client";
import type {
  CharacterProfile,
  OutputSection,
  ProjectOutputs,
  ProjectOutputSurface,
  WorldSheet,
} from "../api/schemas";
import { useAuth } from "../auth/useAuth";
import { EmptyState, LoadingMessage } from "../components/Feedback";
import { formatDateTime, formatRunStatus } from "../formatting/display";
import type { ProjectSummary } from "../projects/projectStore";
import { readableOutputItems } from "./readableOutput";

type OutputSurface =
  | "characters"
  | "world"
  | "timeline"
  | "scenes"
  | "continuity"
  | "prompts"
  | "exports";

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

export function DeveloperPreviewToggle({
  children,
}: {
  children: ReactNode;
}) {
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
        <EmptyState title={processingActive ? "Processing project output" : "No processed output yet"}>
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
            outputs.latest_engine_run
              ? formatRunStatus(outputs.latest_engine_run.status)
              : "No run"
          }
        />
        <Metric label="Chapters" value={outputs.canon.chapters.toLocaleString()} />
        <Metric label="Scenes" value={outputs.canon.scenes.toLocaleString()} />
        <Metric
          label="Evidence"
          value={outputs.canon.evidence_anchor_count.toLocaleString()}
        />
        <Metric label="Snapshot" value={formatDateTime(outputs.canon.created_at)} />
      </dl>
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
      status: mergeSection(existingProfile.status, profile.status),
      current_goal: mergeSection(existingProfile.current_goal, profile.current_goal),
      current_equipment: mergeSection(existingProfile.current_equipment, profile.current_equipment),
      current_abilities: mergeSection(existingProfile.current_abilities, profile.current_abilities),
      current_assets: mergeSection(existingProfile.current_assets, profile.current_assets),
      territory: mergeSection(existingProfile.territory, profile.territory),
      relationships: mergeSection(existingProfile.relationships, profile.relationships),
      current_limitations: mergeSection(existingProfile.current_limitations, profile.current_limitations),
      recent_changes: mergeSection(existingProfile.recent_changes, profile.recent_changes),
      evidence_summary: mergedEvidenceSummary(existingProfile.evidence_summary, profile.evidence_summary),
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
  const identitySections = characterIdentitySections(profile);
  const recentChanges = characterRecentChanges(profile);
  return (
    <article className="profile-card">
      <header>
        <h3>{profile.display_name}</h3>
        <p>{profile.subtitle}</p>
      </header>
      <div className="profile-section-grid">
        {identitySections.map((section) => (
          <PanelSection key={section.title} section={section} />
        ))}
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

function characterIdentitySections(profile: CharacterProfile): OutputSection[] {
  const readableRecentChanges = readableOutputItems(profile.recent_changes.items);
  return ["Race", "Gender"].map((title) => {
    const values = valuesForLabel(readableRecentChanges, title);
    return {
      title,
      items: values.length > 0 ? values : ["Unknown"],
    };
  });
}

function characterRecentChanges(profile: CharacterProfile): OutputSection {
  return {
    title: profile.recent_changes.title,
    items: readableOutputItems(profile.recent_changes.items).filter(
      (item) => !item.startsWith("Name: ") && !item.startsWith("Race: ") && !item.startsWith("Gender: "),
    ),
  };
}

function valuesForLabel(items: string[], label: string): string[] {
  const prefix = `${label}: `;
  return items
    .filter((item) => item.startsWith(prefix))
    .map((item) => item.slice(prefix.length))
    .filter((item, index, allItems) => allItems.indexOf(item) === index);
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

function chapterSpreadLabel(
  counts: ProjectOutputs["canon"]["chapter_scene_counts"],
): string {
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
