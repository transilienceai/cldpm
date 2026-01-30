/**
 * Configuration loading and saving functions.
 */

import { readFile, writeFile, readdir, stat, access } from "node:fs/promises";
import { join } from "node:path";
import {
  CpmConfigSchema,
  type CpmConfig,
  ProjectConfigSchema,
  type ProjectConfig,
  ComponentMetadataSchema,
  type ComponentMetadata,
  type ComponentType,
  getSingularType,
  createComponentDependencies,
} from "../schemas/index.js";

/**
 * Load cpm.json from a repository root.
 */
export async function loadCpmConfig(repoRoot: string): Promise<CpmConfig> {
  const configPath = join(repoRoot, "cpm.json");

  try {
    const content = await readFile(configPath, "utf-8");
    const data = JSON.parse(content);
    return CpmConfigSchema.parse(data);
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") {
      throw new Error(`cpm.json not found at ${repoRoot}`);
    }
    throw error;
  }
}

/**
 * Save cpm.json to a repository root.
 */
export async function saveCpmConfig(
  config: CpmConfig,
  repoRoot: string
): Promise<void> {
  const configPath = join(repoRoot, "cpm.json");
  const content = JSON.stringify(config, null, 2) + "\n";
  await writeFile(configPath, content, "utf-8");
}

/**
 * Load project.json from a project directory.
 */
export async function loadProjectConfig(
  projectPath: string
): Promise<ProjectConfig> {
  const configPath = join(projectPath, "project.json");

  try {
    const content = await readFile(configPath, "utf-8");
    const data = JSON.parse(content);
    return ProjectConfigSchema.parse(data);
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") {
      throw new Error(`project.json not found at ${projectPath}`);
    }
    throw error;
  }
}

/**
 * Save project.json to a project directory.
 */
export async function saveProjectConfig(
  config: ProjectConfig,
  projectPath: string
): Promise<void> {
  const configPath = join(projectPath, "project.json");

  // Exclude undefined/null values
  const cleanConfig = JSON.parse(JSON.stringify(config));

  const content = JSON.stringify(cleanConfig, null, 2) + "\n";
  await writeFile(configPath, content, "utf-8");
}

/**
 * Get the path to a project by name.
 */
export async function getProjectPath(
  projectName: string,
  repoRoot: string
): Promise<string | null> {
  const config = await loadCpmConfig(repoRoot);
  const projectPath = join(repoRoot, config.projectsDir, projectName);

  try {
    await access(join(projectPath, "project.json"));
    return projectPath;
  } catch {
    return null;
  }
}

/**
 * List all projects in a repository.
 */
export async function listProjects(
  repoRoot: string
): Promise<{ name: string; path: string; config: ProjectConfig }[]> {
  const cpmConfig = await loadCpmConfig(repoRoot);
  const projectsDir = join(repoRoot, cpmConfig.projectsDir);

  const projects: { name: string; path: string; config: ProjectConfig }[] = [];

  try {
    const entries = await readdir(projectsDir, { withFileTypes: true });

    for (const entry of entries) {
      if (entry.isDirectory()) {
        const projectPath = join(projectsDir, entry.name);
        try {
          const config = await loadProjectConfig(projectPath);
          projects.push({
            name: config.name,
            path: projectPath,
            config,
          });
        } catch {
          // Not a valid project, skip
        }
      }
    }
  } catch {
    // Projects directory doesn't exist
  }

  return projects;
}

/**
 * Load component metadata.
 */
export async function loadComponentMetadata(
  compType: ComponentType,
  compName: string,
  repoRoot: string
): Promise<ComponentMetadata | null> {
  const config = await loadCpmConfig(repoRoot);
  const compPath = join(repoRoot, config.sharedDir, compType, compName);

  try {
    await access(compPath);
  } catch {
    return null;
  }

  const singular = getSingularType(compType);
  const metadataPath = join(compPath, `${singular}.json`);

  try {
    const content = await readFile(metadataPath, "utf-8");
    const data = JSON.parse(content);
    return ComponentMetadataSchema.parse(data);
  } catch {
    // No metadata file, return minimal metadata
    return {
      name: compName,
      dependencies: createComponentDependencies(),
    };
  }
}

/**
 * Save component metadata.
 */
export async function saveComponentMetadata(
  metadata: ComponentMetadata,
  compType: ComponentType,
  compName: string,
  repoRoot: string
): Promise<void> {
  const config = await loadCpmConfig(repoRoot);
  const compPath = join(repoRoot, config.sharedDir, compType, compName);
  const singular = getSingularType(compType);
  const metadataPath = join(compPath, `${singular}.json`);

  const content = JSON.stringify(metadata, null, 2) + "\n";
  await writeFile(metadataPath, content, "utf-8");
}

/**
 * Check if a path exists.
 */
export async function pathExists(path: string): Promise<boolean> {
  try {
    await access(path);
    return true;
  } catch {
    return false;
  }
}

/**
 * Check if a path is a directory.
 */
export async function isDirectory(path: string): Promise<boolean> {
  try {
    const stats = await stat(path);
    return stats.isDirectory();
  } catch {
    return false;
  }
}
