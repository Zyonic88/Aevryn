import { useQuery } from "@tanstack/react-query";
import { NavLink } from "react-router-dom";

import { apiClient } from "../api/client";
import type { ProjectOutputs } from "../api/schemas";
import { useAuth } from "../auth/useAuth";
import { EmptyState, LoadingMessage } from "../components/Feedback";
import { formatDateTime, formatRunStatus } from "../formatting/display";
import {
  compactIdentityReviewItems,
  identityReviewDetails as identityReviewDetailsLabel,
  identityReviewKey,
  identityReviewTitle,
  translationReviewDetails,
  translationReviewKey,
} from "../output/languageIdentityDisplay";
import type { ProjectSummary } from "../projects/projectStore";

export function OverviewWorkspaceView({ project }: { project: ProjectSummary }) {
  const { session } = useAuth();
  const outputsQuery = useQuery({
    queryKey: ["project-outputs", project.id, session?.session_token],
    queryFn: () => apiClient.projectOutputs(project.id, requireSessionToken(session), nowUtc()),
    enabled: Boolean(session?.session_token),
  });

  return (
    <div className="workspace-view-stack">
      <div>
        <p className="eyebrow">Overview</p>
        <h2>Overview</h2>
      </div>

      {outputsQuery.isLoading ? <LoadingMessage>Loading project overview.</LoadingMessage> : null}
      {outputsQuery.error ? (
        <EmptyState title="Overview unavailable">
          Aevryn could not load the latest processed project state.
        </EmptyState>
      ) : null}
      {outputsQuery.data ? (
        <ProjectOverview project={project} outputs={outputsQuery.data} />
      ) : null}
      {!outputsQuery.isLoading && !outputsQuery.error && !outputsQuery.data ? (
        <EmptyState title="No project output">
          Process a saved import to create project output for this workspace.
        </EmptyState>
      ) : null}
    </div>
  );
}

function ProjectOverview({
  project,
  outputs,
}: {
  project: ProjectSummary;
  outputs: ProjectOutputs;
}) {
  const activeSurfaces = outputs.surfaces.filter((surface) => surface.item_count > 0);
  const nextStep = recommendedNextStep(project.id, outputs);
  return (
    <>
      <section className="project-panel" aria-label="Project state overview">
        <h2>{project.name}</h2>
        <dl className="metric-grid">
          <Metric label="State" value={formatRunStatus(outputs.status)} />
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
          <Metric label="Evidence" value={outputs.canon.evidence_anchor_count.toLocaleString()} />
          <Metric label="Snapshot" value={snapshotLabel(outputs)} />
        </dl>
        <NavLink className="secondary-button" to={`/projects/${project.id}/monitoring`}>
          View monitoring
        </NavLink>
      </section>

      <section className="project-panel" aria-label="Recommended next step">
        <h2>Recommended Next Step</h2>
        <div className="overview-next-step">
          <div>
            <strong>{nextStep.title}</strong>
            <p>{nextStep.body}</p>
          </div>
          <NavLink className="secondary-button" to={nextStep.to}>
            {nextStep.action}
          </NavLink>
        </div>
      </section>

      <section className="project-panel" aria-label="Workspace quick actions">
        <h2>Quick Actions</h2>
        <div className="quick-action-grid">
          {overviewActions(project.id, outputs).map((action) => (
            <NavLink key={action.to} to={action.to}>
              <strong>{action.title}</strong>
              <span>{action.detail}</span>
            </NavLink>
          ))}
        </div>
      </section>

      <section className="project-panel" aria-label="Workspace output overview">
        <h2>Workspace Output</h2>
        {activeSurfaces.length > 0 ? (
          <div className="compact-list">
            {activeSurfaces.map((surface) => (
              <div className="compact-row" key={surface.surface}>
                <strong>{surface.title}</strong>
                <span>{surface.summary}</span>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState title="No workspace output yet">
            Aevryn has not created readable workspace output for this project.
          </EmptyState>
        )}
      </section>

      <section className="project-panel" aria-label="Language and identity overview">
        <h2>Language and Identity</h2>
        <dl className="metric-grid">
          <Metric
            label="Translation"
            value={`${outputs.language_identity.translation_unit_count.toLocaleString()} scenes`}
          />
          <Metric
            label="Resolved"
            value={outputs.language_identity.identity_resolved_count.toLocaleString()}
          />
          <Metric
            label="Review"
            value={identityReviewCount(outputs.language_identity).toLocaleString()}
          />
        </dl>
        {outputs.language_identity.identity_review_items.length > 0 ? (
          <details className="identity-review-panel">
            <summary>Identity Review</summary>
            <div className="compact-list" aria-label="Identity review items">
              {compactIdentityReviewItems(outputs.language_identity.identity_review_items, 6).map((item) => (
                <div className="compact-row" key={identityReviewKey(item)}>
                  <strong>{identityReviewTitle(item)}</strong>
                  <span>{identityReviewDetails(item)}</span>
                </div>
              ))}
            </div>
          </details>
        ) : (
          <p className="result-summary">No identity review items in the latest snapshot.</p>
        )}
        {outputs.language_identity.translation_review_items.length > 0 ? (
          <details className="identity-review-panel">
            <summary>Translation Review</summary>
            <div className="compact-list" aria-label="Translation review items">
              {outputs.language_identity.translation_review_items.slice(0, 6).map((item) => (
                <div className="compact-row" key={translationReviewKey(item)}>
                  <strong>{item.issue_label}</strong>
                  <span>{translationReviewDetails(item, "held for review")}</span>
                </div>
              ))}
            </div>
          </details>
        ) : null}
      </section>
    </>
  );
}

function recommendedNextStep(projectId: string, outputs: ProjectOutputs): OverviewAction {
  const runStatus = outputs.latest_engine_run?.status ?? outputs.status;
  if (!outputs.latest_import) {
    return {
      title: "Import chapters",
      body: "Add source chapters before Aevryn can build Canon-backed outputs.",
      action: "Open import",
      to: `/projects/${projectId}/import`,
    };
  }
  if (runStatus === "pending" || runStatus === "running") {
    return {
      title: "Watch processing",
      body: "Aevryn is still processing the latest import. Monitoring shows API-provided workflow state.",
      action: "View monitoring",
      to: `/projects/${projectId}/monitoring`,
    };
  }
  if (!outputs.canon.available) {
    return {
      title: "Process saved import",
      body: "The project has import metadata, but no accepted Canon snapshot is ready yet.",
      action: "Open import",
      to: `/projects/${projectId}/import`,
    };
  }
  if (identityReviewCount(outputs.language_identity) > 0) {
    return {
      title: "Review identity",
      body: "Aevryn found references that need human review before they should influence creator-facing output.",
      action: "Open characters",
      to: `/projects/${projectId}/characters`,
    };
  }
  if (surfaceItemCount(outputs, "prompts") > 0) {
    return {
      title: "Prepare prompt packs",
      body: "Canon-backed scene context is available for image, narration, camera, and animation prompts.",
      action: "Open prompt packs",
      to: `/projects/${projectId}/prompts`,
    };
  }
  return {
    title: "Review project output",
    body: "Aevryn has processed this project. Review workspace sections before exporting.",
    action: "Open scenes",
    to: `/projects/${projectId}/scenes`,
  };
}

function overviewActions(projectId: string, outputs: ProjectOutputs): OverviewAction[] {
  return [
    {
      title: "Story",
      body: "",
      detail: outputs.latest_import ? "Story metadata ready" : "Create or select a story",
      action: "Open story",
      to: `/projects/${projectId}/story`,
    },
    {
      title: "Import",
      body: "",
      detail: outputs.latest_import ? "Latest import saved" : "Add chapters",
      action: "Open import",
      to: `/projects/${projectId}/import`,
    },
    {
      title: "Characters",
      body: "",
      detail: `${surfaceItemCount(outputs, "characters").toLocaleString()} profiles`,
      action: "Open characters",
      to: `/projects/${projectId}/characters`,
    },
    {
      title: "Prompt Packs",
      body: "",
      detail: `${surfaceItemCount(outputs, "prompts").toLocaleString()} scenes ready`,
      action: "Open prompt packs",
      to: `/projects/${projectId}/prompts`,
    },
    {
      title: "Exports",
      body: "",
      detail: outputs.canon.available ? "Snapshot export available" : "No snapshot yet",
      action: "Open exports",
      to: `/projects/${projectId}/exports`,
    },
  ];
}

type OverviewAction = {
  title: string;
  body: string;
  detail?: string;
  action: string;
  to: string;
};

function surfaceItemCount(outputs: ProjectOutputs, surface: string): number {
  return outputs.surfaces.find((item) => item.surface === surface)?.item_count ?? 0;
}

function snapshotLabel(outputs: ProjectOutputs): string {
  if (!outputs.canon.available) {
    return "No snapshot";
  }
  return formatDateTime(outputs.canon.created_at);
}

function identityReviewCount(summary: ProjectOutputs["language_identity"]): number {
  return (
    summary.identity_ambiguous_count +
    summary.identity_unresolved_count +
    summary.translation_review_count
  );
}

function identityReviewDetails(
  item: ProjectOutputs["language_identity"]["identity_review_items"][number],
): string {
  return identityReviewDetailsLabel(item, identityActionLabel(item.status));
}

function identityActionLabel(status: string): string {
  if (status === "ambiguous") {
    return "held for review";
  }
  if (status === "unresolved") {
    return "left unresolved";
  }
  return "marked for review";
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
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
