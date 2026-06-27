import { NavLink, Navigate, useParams } from "react-router-dom";

import { EmptyState } from "../components/Feedback";
import { readProjects } from "../projects/projectStore";
import { CharacterWorkspaceView } from "./CharacterWorkspaceView";
import { ImportWorkspaceView } from "./ImportWorkspaceView";

const workspaceTabs = [
  { id: "overview", label: "Overview" },
  { id: "import", label: "Import" },
  { id: "characters", label: "Characters" },
  { id: "world", label: "World" },
  { id: "timeline", label: "Timeline" },
  { id: "scenes", label: "Scenes" },
  { id: "continuity", label: "Continuity" },
  { id: "prompts", label: "Prompt Packs" },
  { id: "exports", label: "Exports" },
] as const;

type WorkspaceTabId = (typeof workspaceTabs)[number]["id"];

export function ProjectWorkspacePage() {
  const { projectId, tabId = "overview" } = useParams();
  const project = readProjects().find((candidate) => candidate.id === projectId);
  if (!project) {
    return <Navigate to="/dashboard" replace />;
  }

  const activeTab = findWorkspaceTab(tabId);

  return (
    <div className="workspace-shell">
      <aside className="workspace-sidebar">
        <div className="workspace-project">
          <p className="eyebrow">Project shell</p>
          <h1>{project.name}</h1>
        </div>
        <nav aria-label="Workspace sections" className="workspace-nav">
          {workspaceTabs.map((tab) => (
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
  project: ReturnType<typeof readProjects>[number];
}) {
  if (tabId === "import") {
    return <ImportWorkspaceView project={project} />;
  }
  if (tabId === "characters") {
    return <CharacterWorkspaceView project={project} />;
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
      </div>
    </>
  );
}

function findWorkspaceTab(tabId: string): (typeof workspaceTabs)[number] | null {
  return workspaceTabs.find((tab) => tab.id === tabId) ?? null;
}

function placeholderTitle(tabId: WorkspaceTabId): string {
  if (tabId === "overview") {
    return "Workspace shell is connected.";
  }
  return "Engine output view placeholder.";
}

function placeholderBody(tabId: WorkspaceTabId): string {
  if (tabId === "overview") {
    return "This page proves routing, sidebar navigation, and project shell state without duplicating engine logic.";
  }
  return "This section will render API view models after the import workflow is hardened.";
}
