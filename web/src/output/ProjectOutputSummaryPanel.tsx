import { useQuery } from "@tanstack/react-query";
import type { ReactNode } from "react";

import { apiClient } from "../api/client";
import type { ProjectOutputs, ProjectOutputSurface } from "../api/schemas";
import { useAuth } from "../auth/useAuth";
import { EmptyState, LoadingMessage } from "../components/Feedback";
import { formatDateTime, formatRunStatus } from "../formatting/display";
import type { ProjectSummary } from "../projects/projectStore";

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
    return (
      <section className="project-panel" aria-label="Processed project output">
        <h2>Processed Project Results</h2>
        <EmptyState title="No processed output yet">
          Save an import, submit processing, and wait for a canon snapshot.
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
        <Metric label="Source" value={outputs.latest_import?.filename ?? "Latest import"} />
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
    </section>
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
