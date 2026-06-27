import type { Project } from "../api/schemas";
import type { ProjectSummary } from "./projectStore";

export function projectSummaryFromApiProject(project: Project): ProjectSummary {
  return {
    id: project.project_id,
    name: project.name,
    updatedAt: project.updated_at,
  };
}
