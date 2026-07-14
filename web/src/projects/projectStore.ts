const DEFAULT_PROJECT_NAME = "Untitled Story Project";
const MAX_PROJECT_NAME_LENGTH = 120;

export type ProjectSummary = {
  id: string;
  name: string;
  updatedAt: string;
};

export type ProjectFactoryOptions = {
  now?: Date;
  randomUuid?: string;
};

export function defaultProjectName(): string {
  return DEFAULT_PROJECT_NAME;
}

export function normalizeProjectName(name: string): string {
  return name.trim().replace(/\s+/g, " ").slice(0, MAX_PROJECT_NAME_LENGTH);
}

export function createProjectShell(
  name: string,
  options: ProjectFactoryOptions = {},
): ProjectSummary {
  const normalizedName = normalizeProjectName(name);
  if (!normalizedName) {
    throw new Error("Project name is required.");
  }

  const timestamp = (options.now ?? new Date()).toISOString();
  const uuid = options.randomUuid ?? createUuid();
  const project: ProjectSummary = {
    id: `project_${uuid.replaceAll("-", "_")}`,
    name: normalizedName,
    updatedAt: timestamp,
  };
  return project;
}

function createUuid(): string {
  if (typeof globalThis.crypto?.randomUUID === "function") {
    return globalThis.crypto.randomUUID();
  }
  throw new Error("Browser crypto.randomUUID is required to create a project.");
}
