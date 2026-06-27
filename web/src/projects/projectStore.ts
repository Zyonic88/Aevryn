const PROJECT_STORAGE_KEY = "aevryn.projects";
const DEFAULT_PROJECT_NAME = "Untitled Story Project";
const MAX_PROJECT_NAME_LENGTH = 120;
const MAX_STORED_PROJECTS = 100;

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

export function readProjects(storage: Storage = window.localStorage): ProjectSummary[] {
  const rawProjects = safeGetItem(storage, PROJECT_STORAGE_KEY);
  if (!rawProjects) {
    return [];
  }
  try {
    const parsed = JSON.parse(rawProjects);
    if (!Array.isArray(parsed)) {
      safeRemoveItem(storage, PROJECT_STORAGE_KEY);
      return [];
    }
    return parsed.filter(isProjectSummary).slice(0, MAX_STORED_PROJECTS);
  } catch {
    safeRemoveItem(storage, PROJECT_STORAGE_KEY);
    return [];
  }
}

export function writeProjects(
  projects: ProjectSummary[],
  storage: Storage = window.localStorage,
): boolean {
  return safeSetItem(
    storage,
    PROJECT_STORAGE_KEY,
    JSON.stringify(projects.slice(0, MAX_STORED_PROJECTS)),
  );
}

export function createProject(
  name: string,
  projects: ProjectSummary[],
  options: ProjectFactoryOptions = {},
): ProjectSummary[] {
  const project = createProjectShell(name, options);
  return [project, ...projects.filter((candidate) => candidate.id !== project.id)].slice(
    0,
    MAX_STORED_PROJECTS,
  );
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
  throw new Error("Browser crypto.randomUUID is required to create a project shell.");
}

function isProjectSummary(value: unknown): value is ProjectSummary {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const candidate = value as ProjectSummary;
  return (
    typeof candidate.id === "string" &&
    candidate.id.startsWith("project_") &&
    typeof candidate.name === "string" &&
    candidate.name.trim().length > 0 &&
    typeof candidate.updatedAt === "string"
  );
}

function safeGetItem(storage: Storage, key: string): string | null {
  try {
    return storage.getItem(key);
  } catch {
    return null;
  }
}

function safeSetItem(storage: Storage, key: string, value: string): boolean {
  try {
    storage.setItem(key, value);
    return true;
  } catch {
    return false;
  }
}

function safeRemoveItem(storage: Storage, key: string): boolean {
  try {
    storage.removeItem(key);
    return true;
  } catch {
    return false;
  }
}
