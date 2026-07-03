import { useQuery } from "@tanstack/react-query";
import { NavLink, Navigate, useParams } from "react-router-dom";

import { ApiError, apiClient } from "../api/client";
import { useAuth } from "../auth/useAuth";
import { EmptyState, ErrorMessage, LoadingMessage } from "../components/Feedback";
import { projectSummaryFromApiProject } from "../projects/projectMapping";
import { readProjects, type ProjectSummary } from "../projects/projectStore";
import { CharacterWorkspaceView } from "./CharacterWorkspaceView";
import { ContinuityWorkspaceView } from "./ContinuityWorkspaceView";
import { ExportWorkspaceView } from "./ExportWorkspaceView";
import { ImportWorkspaceView } from "./ImportWorkspaceView";
import { MonitoringWorkspaceView } from "./MonitoringWorkspaceView";
import { OverviewWorkspaceView } from "./OverviewWorkspaceView";
import { PromptWorkspaceView } from "./PromptWorkspaceView";
import { SceneWorkspaceView } from "./SceneWorkspaceView";
import { SettingsWorkspaceView } from "./SettingsWorkspaceView";
import { StoryWorkspaceView } from "./StoryWorkspaceView";
import { TimelineWorkspaceView } from "./TimelineWorkspaceView";
import { WorldWorkspaceView } from "./WorldWorkspaceView";

const workspaceTabs = [
  { id: "overview", label: "Overview" },
  { id: "monitoring", label: "Monitoring" },
  { id: "story", label: "Story" },
  { id: "import", label: "Import" },
  { id: "characters", label: "Characters" },
  { id: "world", label: "World" },
  { id: "timeline", label: "Timeline" },
  { id: "scenes", label: "Scenes" },
  { id: "continuity", label: "Continuity" },
  { id: "prompts", label: "Prompt Packs" },
  { id: "exports", label: "Exports" },
  { id: "settings", label: "Settings" },
] as const;

type WorkspaceTabId = (typeof workspaceTabs)[number]["id"];

const visibleWorkspaceTabs = workspaceTabs.filter((tab) => tab.id !== "monitoring");

export function ProjectWorkspacePage() {
  const { session } = useAuth();
  const { projectId, tabId = "overview" } = useParams();
  const projectQuery = useQuery({
    queryKey: ["project", projectId, session?.session_token],
    queryFn: () =>
      apiClient.getProject(requireProjectId(projectId), requireSessionToken(session), new Date().toISOString()),
    enabled: session !== null && projectId !== undefined,
  });
  const legacyProject = readProjects().find((candidate) => candidate.id === projectId) ?? null;

  if (projectId === undefined) {
    return <Navigate to="/dashboard" replace />;
  }

  const project = projectQuery.data
    ? projectSummaryFromApiProject(projectQuery.data)
    : legacyProject;

  if (projectQuery.isLoading && project === null) {
    return <LoadingMessage>Loading project.</LoadingMessage>;
  }

  if (projectQuery.error && project === null) {
    if (projectQuery.error instanceof ApiError && projectQuery.error.status === 404) {
      return <Navigate to="/dashboard" replace />;
    }
    return <ErrorMessage>{projectQuery.error.message}</ErrorMessage>;
  }

  if (project === null) {
    return <Navigate to="/dashboard" replace />;
  }

  const activeTab = findWorkspaceTab(tabId);

  return (
    <div className="workspace-shell">
      <aside className="workspace-sidebar">
        <div className="workspace-project">
          <p className="eyebrow">Project</p>
          <h1>{project.name}</h1>
        </div>
        <nav aria-label="Workspace sections" className="workspace-nav">
          {visibleWorkspaceTabs.map((tab) => (
            <NavLink key={tab.id} to={`/projects/${project.id}/${tab.id}`}>
              {tab.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <section className="workspace-content">
        {activeTab ? (
          <WorkspaceTabContent tabId={activeTab.id} label={activeTab.label} project={project} />
        ) : (
          <EmptyState title="Unknown workspace section">
            This project route is valid, but the requested section does not exist in the Web Alpha
            Shell.
          </EmptyState>
        )}
      </section>
    </div>
  );
}

function WorkspaceTabContent({
  tabId,
  label,
  project,
}: {
  tabId: WorkspaceTabId;
  label: string;
  project: ProjectSummary;
}) {
  if (tabId === "overview") {
    return <OverviewWorkspaceView project={project} />;
  }
  if (tabId === "import") {
    return <ImportWorkspaceView project={project} />;
  }
  if (tabId === "monitoring") {
    return <MonitoringWorkspaceView project={project} />;
  }
  if (tabId === "story") {
    return <StoryWorkspaceView project={project} />;
  }
  if (tabId === "characters") {
    return <CharacterWorkspaceView project={project} />;
  }
  if (tabId === "world") {
    return <WorldWorkspaceView project={project} />;
  }
  if (tabId === "timeline") {
    return <TimelineWorkspaceView project={project} />;
  }
  if (tabId === "scenes") {
    return <SceneWorkspaceView project={project} />;
  }
  if (tabId === "continuity") {
    return <ContinuityWorkspaceView project={project} />;
  }
  if (tabId === "prompts") {
    return <PromptWorkspaceView project={project} />;
  }
  if (tabId === "exports") {
    return <ExportWorkspaceView project={project} />;
  }
  if (tabId === "settings") {
    return <SettingsWorkspaceView project={project} />;
  }

  return <WorkspacePlaceholder tabId={tabId} label={label} />;
}

function WorkspacePlaceholder({ tabId, label }: { tabId: WorkspaceTabId; label: string }) {
  return (
    <>
      <p className="eyebrow">{label}</p>
      <h2>{label}</h2>
      <div className="placeholder-panel">
        <h3>{placeholderTitle(tabId)}</h3>
        <p>{placeholderBody(tabId)}</p>
        {tabId === "overview" ? (
          <NavLink className="secondary-button" to="monitoring">
            View monitoring
          </NavLink>
        ) : null}
      </div>
    </>
  );
}

function findWorkspaceTab(tabId: string): (typeof workspaceTabs)[number] | null {
  return workspaceTabs.find((tab) => tab.id === tabId) ?? null;
}

function placeholderTitle(tabId: WorkspaceTabId): string {
  if (tabId === "overview") {
    return "Project workspace is ready.";
  }
  return "Engine output view placeholder.";
}

function placeholderBody(tabId: WorkspaceTabId): string {
  if (tabId === "overview") {
    return "Use Story and Import to add chapters. Monitoring is available when you need workflow diagnostics.";
  }
  return "This workspace section is not available yet.";
}

function requireProjectId(projectId: string | undefined): string {
  if (projectId === undefined) {
    throw new Error("Aevryn project id is required.");
  }
  return projectId;
}

function requireSessionToken(session: { session_token: string } | null): string {
  if (!session) {
    throw new Error("Aevryn session is required.");
  }
  return session.session_token;
}
