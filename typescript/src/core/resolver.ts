/**
 * Project and component resolution functions.
 */

import { readdir, lstat } from "node:fs/promises";
import { join } from "node:path";
import {
  type ComponentType,
  ComponentTypes,
  type ResolvedComponent,
  type ProjectConfig,
} from "../schemas/index.js";
import {
  loadCldpmConfig,
  loadProjectConfig,
  loadComponentMetadata,
  getProjectPath,
  pathExists,
} from "./config.js";

/**
 * Resolved project with all components.
 */
export interface ResolvedProject {
  name: string;
  path: string;
  config: ProjectConfig;
  shared: Record<ComponentType, ResolvedComponent[]>;
  local: Record<ComponentType, ResolvedComponent[]>;
}

/**
 * Resolve a shared component.
 */
export async function resolveComponent(
  compType: ComponentType,
  compName: string,
  sharedDir: string
): Promise<ResolvedComponent | null> {
  const compPath = join(sharedDir, compType, compName);

  if (!(await pathExists(compPath))) {
    return null;
  }

  const files: string[] = [];
  try {
    const entries = await readdir(compPath);
    files.push(...entries.filter((f) => !f.startsWith(".")));
  } catch {
    return null;
  }

  return {
    name: compName,
    type: "shared",
    sourcePath: compPath,
    files,
  };
}

/**
 * Resolve a local component in a project.
 */
export async function resolveLocalComponent(
  compType: ComponentType,
  compName: string,
  projectPath: string
): Promise<ResolvedComponent | null> {
  const compPath = join(projectPath, ".claude", compType, compName);

  if (!(await pathExists(compPath))) {
    return null;
  }

  // Check if it's a symlink
  try {
    const stats = await lstat(compPath);
    if (stats.isSymbolicLink()) {
      return null; // Symlinks are shared components, not local
    }
  } catch {
    return null;
  }

  const files: string[] = [];
  try {
    const entries = await readdir(compPath);
    files.push(...entries.filter((f) => !f.startsWith(".")));
  } catch {
    return null;
  }

  return {
    name: compName,
    type: "local",
    sourcePath: join(".claude", compType, compName),
    files,
  };
}

/**
 * Get all local components in a project.
 */
export async function getLocalComponentsInProject(
  projectPath: string
): Promise<Record<ComponentType, ResolvedComponent[]>> {
  const result: Record<ComponentType, ResolvedComponent[]> = {
    skills: [],
    agents: [],
    hooks: [],
    rules: [],
  };

  for (const compType of ComponentTypes) {
    const typeDir = join(projectPath, ".claude", compType);

    if (!(await pathExists(typeDir))) {
      continue;
    }

    try {
      const entries = await readdir(typeDir, { withFileTypes: true });

      for (const entry of entries) {
        if (entry.isDirectory() && !entry.name.startsWith(".")) {
          const compPath = join(typeDir, entry.name);

          // Check if it's a symlink
          const stats = await lstat(compPath);
          if (stats.isSymbolicLink()) {
            continue; // Skip symlinks
          }

          const component = await resolveLocalComponent(
            compType,
            entry.name,
            projectPath
          );
          if (component) {
            result[compType].push(component);
          }
        }
      }
    } catch {
      // Directory doesn't exist or error reading
    }
  }

  return result;
}

/**
 * Resolve a project with all its components.
 */
export async function resolveProject(
  projectNameOrPath: string,
  repoRoot: string
): Promise<ResolvedProject> {
  const cldpmConfig = await loadCldpmConfig(repoRoot);

  // Determine project path
  let projectPath: string;
  if (
    projectNameOrPath.includes("/") ||
    projectNameOrPath.includes("\\")
  ) {
    // It's a path
    projectPath = projectNameOrPath.startsWith("/")
      ? projectNameOrPath
      : join(repoRoot, projectNameOrPath);
  } else {
    // It's a name
    const foundPath = await getProjectPath(projectNameOrPath, repoRoot);
    if (!foundPath) {
      throw new Error(`Project not found: ${projectNameOrPath}`);
    }
    projectPath = foundPath;
  }

  const projectConfig = await loadProjectConfig(projectPath);
  const sharedDir = join(repoRoot, cldpmConfig.sharedDir);

  // Resolve shared components
  const shared: Record<ComponentType, ResolvedComponent[]> = {
    skills: [],
    agents: [],
    hooks: [],
    rules: [],
  };

  for (const compType of ComponentTypes) {
    const deps = projectConfig.dependencies[compType] || [];
    for (const compName of deps) {
      const component = await resolveComponent(compType, compName, sharedDir);
      if (component) {
        shared[compType].push(component);
      }
    }
  }

  // Resolve local components
  const local = await getLocalComponentsInProject(projectPath);

  return {
    name: projectConfig.name,
    path: projectPath,
    config: projectConfig,
    shared,
    local,
  };
}

/**
 * List all shared components in a repository.
 */
export async function listSharedComponents(
  repoRoot: string
): Promise<Record<ComponentType, string[]>> {
  const cldpmConfig = await loadCldpmConfig(repoRoot);
  const sharedDir = join(repoRoot, cldpmConfig.sharedDir);

  const result: Record<ComponentType, string[]> = {
    skills: [],
    agents: [],
    hooks: [],
    rules: [],
  };

  for (const compType of ComponentTypes) {
    const typeDir = join(sharedDir, compType);

    if (!(await pathExists(typeDir))) {
      continue;
    }

    try {
      const entries = await readdir(typeDir, { withFileTypes: true });

      for (const entry of entries) {
        if (entry.isDirectory() && !entry.name.startsWith(".")) {
          result[compType].push(entry.name);
        }
      }
    } catch {
      // Directory doesn't exist or error reading
    }
  }

  return result;
}

/**
 * Resolve all dependencies for a component (including transitive).
 */
export async function resolveComponentDependencies(
  compType: ComponentType,
  compName: string,
  repoRoot: string,
  visited: Set<string> = new Set()
): Promise<Array<[ComponentType, string]>> {
  const key = `${compType}:${compName}`;
  if (visited.has(key)) {
    return [];
  }
  visited.add(key);

  const metadata = await loadComponentMetadata(compType, compName, repoRoot);
  if (!metadata) {
    return [];
  }

  const deps: Array<[ComponentType, string]> = [];

  for (const depType of ComponentTypes) {
    const depNames = metadata.dependencies[depType] || [];
    for (const depName of depNames) {
      deps.push([depType, depName]);

      // Recursively resolve transitive dependencies
      const transitive = await resolveComponentDependencies(
        depType,
        depName,
        repoRoot,
        visited
      );
      deps.push(...transitive);
    }
  }

  return deps;
}

/**
 * Get all dependencies for a component organized by type.
 */
export async function getAllDependenciesForComponent(
  compType: ComponentType,
  compName: string,
  repoRoot: string
): Promise<Record<ComponentType, string[]>> {
  const deps = await resolveComponentDependencies(compType, compName, repoRoot);

  const result: Record<ComponentType, string[]> = {
    skills: [],
    agents: [],
    hooks: [],
    rules: [],
  };

  for (const [depType, depName] of deps) {
    if (!result[depType].includes(depName)) {
      result[depType].push(depName);
    }
  }

  return result;
}
