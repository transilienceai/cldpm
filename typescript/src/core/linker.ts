/**
 * Symlink management functions.
 */

import {
  readdir,
  lstat,
  symlink,
  unlink,
  readFile,
  writeFile,
  mkdir,
} from "node:fs/promises";
import { join, relative } from "node:path";
import {
  type ComponentType,
  ComponentTypes,
} from "../schemas/index.js";
import {
  loadCldpmConfig,
  loadProjectConfig,
  pathExists,
} from "./config.js";

const CLDPM_GITIGNORE_HEADER = "# CLDPM shared components (auto-generated)\n";

/**
 * Create a symlink.
 */
export async function createSymlink(
  source: string,
  target: string
): Promise<boolean> {
  try {
    // Check if target already exists
    if (await pathExists(target)) {
      const stats = await lstat(target);
      if (stats.isSymbolicLink()) {
        // Remove existing symlink
        await unlink(target);
      } else {
        // Not a symlink, don't overwrite
        return false;
      }
    }

    // Ensure parent directory exists
    const parentDir = join(target, "..");
    await mkdir(parentDir, { recursive: true });

    // Create relative symlink
    const relativeSource = relative(parentDir, source);
    await symlink(relativeSource, target);
    return true;
  } catch {
    return false;
  }
}

/**
 * Remove all symlinks from a project.
 */
export async function removeProjectLinks(projectPath: string): Promise<void> {
  for (const compType of ComponentTypes) {
    const typeDir = join(projectPath, ".claude", compType);

    if (!(await pathExists(typeDir))) {
      continue;
    }

    try {
      const entries = await readdir(typeDir, { withFileTypes: true });

      for (const entry of entries) {
        if (entry.isDirectory() || entry.isSymbolicLink()) {
          const entryPath = join(typeDir, entry.name);
          const stats = await lstat(entryPath);

          if (stats.isSymbolicLink()) {
            await unlink(entryPath);
          }
        }
      }
    } catch {
      // Error reading directory
    }
  }
}

/**
 * Update .gitignore in a component type directory.
 */
export async function updateComponentGitignore(
  compDir: string,
  symlinks: string[]
): Promise<void> {
  const gitignorePath = join(compDir, ".gitignore");

  if (symlinks.length === 0) {
    // Remove gitignore if it's a CLDPM-generated one
    if (await pathExists(gitignorePath)) {
      try {
        const content = await readFile(gitignorePath, "utf-8");
        if (content.startsWith(CLDPM_GITIGNORE_HEADER)) {
          await unlink(gitignorePath);
        }
      } catch {
        // Ignore errors
      }
    }
    return;
  }

  // Create/update gitignore
  const content = CLDPM_GITIGNORE_HEADER + symlinks.join("\n") + "\n";
  await writeFile(gitignorePath, content, "utf-8");
}

/**
 * Sync symlinks for a project based on its dependencies.
 */
export async function syncProjectLinks(
  projectPath: string,
  repoRoot: string
): Promise<{ created: string[]; missing: string[] }> {
  const cldpmConfig = await loadCldpmConfig(repoRoot);
  const projectConfig = await loadProjectConfig(projectPath);
  const sharedDir = join(repoRoot, cldpmConfig.sharedDir);

  const created: string[] = [];
  const missing: string[] = [];

  // Remove existing symlinks first
  await removeProjectLinks(projectPath);

  // Create symlinks for each component type
  for (const compType of ComponentTypes) {
    const deps = projectConfig.dependencies[compType] || [];
    const typeDir = join(projectPath, ".claude", compType);
    const symlinks: string[] = [];

    // Ensure directory exists
    await mkdir(typeDir, { recursive: true });

    for (const compName of deps) {
      const source = join(sharedDir, compType, compName);
      const target = join(typeDir, compName);

      if (!(await pathExists(source))) {
        missing.push(`${compType}/${compName}`);
        continue;
      }

      const success = await createSymlink(source, target);
      if (success) {
        created.push(`${compType}/${compName}`);
        symlinks.push(compName);
      }
    }

    // Update gitignore
    await updateComponentGitignore(typeDir, symlinks);
  }

  return { created, missing };
}

/**
 * Add a single component link to a project.
 */
export async function addComponentLink(
  projectPath: string,
  compType: ComponentType,
  compName: string,
  repoRoot: string
): Promise<boolean> {
  const cldpmConfig = await loadCldpmConfig(repoRoot);
  const sharedDir = join(repoRoot, cldpmConfig.sharedDir);

  const source = join(sharedDir, compType, compName);
  if (!(await pathExists(source))) {
    return false;
  }

  const typeDir = join(projectPath, ".claude", compType);
  await mkdir(typeDir, { recursive: true });

  const target = join(typeDir, compName);
  const success = await createSymlink(source, target);

  if (success) {
    // Update gitignore
    const symlinks = await getSharedComponentsInDir(typeDir);
    await updateComponentGitignore(typeDir, symlinks);
  }

  return success;
}

/**
 * Remove a component link from a project.
 */
export async function removeComponentLink(
  projectPath: string,
  compType: ComponentType,
  compName: string
): Promise<boolean> {
  const target = join(projectPath, ".claude", compType, compName);

  if (!(await pathExists(target))) {
    return false;
  }

  try {
    const stats = await lstat(target);
    if (!stats.isSymbolicLink()) {
      return false; // Not a symlink
    }

    await unlink(target);

    // Update gitignore
    const typeDir = join(projectPath, ".claude", compType);
    const symlinks = await getSharedComponentsInDir(typeDir);
    await updateComponentGitignore(typeDir, symlinks);

    return true;
  } catch {
    return false;
  }
}

/**
 * Get symlinked component names in a directory.
 */
async function getSharedComponentsInDir(typeDir: string): Promise<string[]> {
  const symlinks: string[] = [];

  try {
    const entries = await readdir(typeDir, { withFileTypes: true });

    for (const entry of entries) {
      if (entry.name.startsWith(".")) continue;

      const entryPath = join(typeDir, entry.name);
      const stats = await lstat(entryPath);

      if (stats.isSymbolicLink()) {
        symlinks.push(entry.name);
      }
    }
  } catch {
    // Error reading directory
  }

  return symlinks;
}

/**
 * Get all local (non-symlinked) components in a project.
 */
export async function getLocalComponents(
  projectPath: string
): Promise<Record<ComponentType, string[]>> {
  const result: Record<ComponentType, string[]> = {
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
        if (entry.name.startsWith(".")) continue;

        const entryPath = join(typeDir, entry.name);
        const stats = await lstat(entryPath);

        if (stats.isDirectory() && !stats.isSymbolicLink()) {
          result[compType].push(entry.name);
        }
      }
    } catch {
      // Error reading directory
    }
  }

  return result;
}

/**
 * Get all shared (symlinked) components in a project.
 */
export async function getSharedComponents(
  projectPath: string
): Promise<Record<ComponentType, string[]>> {
  const result: Record<ComponentType, string[]> = {
    skills: [],
    agents: [],
    hooks: [],
    rules: [],
  };

  for (const compType of ComponentTypes) {
    const typeDir = join(projectPath, ".claude", compType);
    result[compType] = await getSharedComponentsInDir(typeDir);
  }

  return result;
}
