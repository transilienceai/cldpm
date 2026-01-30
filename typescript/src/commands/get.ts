/**
 * cldpm get command
 */

import { Command } from "commander";
import { cwd } from "node:process";
import * as path from "node:path";
import * as fs from "node:fs/promises";
import { resolveProject, loadCldpmConfig } from "../core/index.js";
import { error, success, warning, printProjectTree, printProjectJson } from "../utils/index.js";

/**
 * Copy a directory recursively, resolving symlinks to actual files
 */
async function copyDir(src: string, dest: string, resolveSymlinks = true): Promise<void> {
  await fs.mkdir(dest, { recursive: true });
  const entries = await fs.readdir(src, { withFileTypes: true });

  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);

    // Check if it's a symlink using lstat
    const lstat = await fs.lstat(srcPath);

    if (lstat.isSymbolicLink() && resolveSymlinks) {
      // Resolve symlink and copy the actual content
      const realPath = await fs.realpath(srcPath);
      const stat = await fs.stat(realPath);
      if (stat.isDirectory()) {
        await copyDir(realPath, destPath, resolveSymlinks);
      } else {
        await fs.copyFile(realPath, destPath);
      }
    } else if (entry.isDirectory()) {
      await copyDir(srcPath, destPath, resolveSymlinks);
    } else {
      await fs.copyFile(srcPath, destPath);
    }
  }
}

/**
 * Download/copy a local project with all dependencies resolved
 */
async function downloadLocalProject(
  resolved: {
    name: string;
    path: string;
    shared: Record<string, Array<{ name: string }>>;
    local: Record<string, Array<{ name: string }>>;
  },
  repoRoot: string,
  outputDir?: string
): Promise<void> {
  const sourcePath = resolved.path;
  const projectName = resolved.name;

  // Determine target directory
  const targetPath = outputDir
    ? path.resolve(outputDir)
    : path.join(cwd(), projectName);

  // Check if target exists
  try {
    await fs.access(targetPath);
    error(`Target directory already exists: ${targetPath}`);
    process.exit(1);
  } catch {
    // Directory doesn't exist, which is what we want
  }

  // Create target directory
  await fs.mkdir(targetPath, { recursive: true });

  // Load CLDPM config for shared directory path
  const cldpmConfig = await loadCldpmConfig(repoRoot);
  const sharedDir = path.join(repoRoot, cldpmConfig.sharedDir);

  // Copy project files
  const entries = await fs.readdir(sourcePath, { withFileTypes: true });
  for (const entry of entries) {
    const srcPath = path.join(sourcePath, entry.name);
    const destPath = path.join(targetPath, entry.name);

    if (entry.name === ".claude") {
      // Handle .claude directory specially
      await fs.mkdir(destPath, { recursive: true });
      const claudeEntries = await fs.readdir(srcPath, { withFileTypes: true });

      for (const claudeEntry of claudeEntries) {
        const claudeSrcPath = path.join(srcPath, claudeEntry.name);
        const claudeDestPath = path.join(destPath, claudeEntry.name);

        if (["skills", "agents", "hooks", "rules"].includes(claudeEntry.name)) {
          // Create directory
          await fs.mkdir(claudeDestPath, { recursive: true });

          // Copy local (non-symlink) components directly
          const compEntries = await fs.readdir(claudeSrcPath, { withFileTypes: true });
          for (const compEntry of compEntries) {
            if (compEntry.name === ".gitignore") continue;

            const compSrcPath = path.join(claudeSrcPath, compEntry.name);
            const compDestPath = path.join(claudeDestPath, compEntry.name);

            // Check if it's a symlink
            const lstat = await fs.lstat(compSrcPath);
            if (!lstat.isSymbolicLink()) {
              if (compEntry.isDirectory()) {
                await copyDir(compSrcPath, compDestPath, false);
              } else {
                await fs.copyFile(compSrcPath, compDestPath);
              }
            }
          }
        } else if (claudeEntry.isFile()) {
          await fs.copyFile(claudeSrcPath, claudeDestPath);
        } else if (claudeEntry.isDirectory()) {
          await copyDir(claudeSrcPath, claudeDestPath, false);
        }
      }
    } else if (entry.isDirectory()) {
      await copyDir(srcPath, destPath, false);
    } else {
      await fs.copyFile(srcPath, destPath);
    }
  }

  // Copy shared dependencies (resolve symlinks to actual files)
  const depTypes = ["skills", "agents", "hooks", "rules"] as const;
  for (const depType of depTypes) {
    const components = resolved.shared[depType] || [];
    for (const component of components) {
      const compName = component.name;
      const sourceComp = path.join(sharedDir, depType, compName);
      const targetComp = path.join(targetPath, ".claude", depType, compName);

      try {
        await fs.access(sourceComp);
        try {
          await fs.access(targetComp);
          // Already exists, skip
        } catch {
          // Doesn't exist, copy
          const stat = await fs.stat(sourceComp);
          if (stat.isDirectory()) {
            await copyDir(sourceComp, targetComp, false);
          } else {
            await fs.copyFile(sourceComp, targetComp);
          }
        }
      } catch {
        // Source doesn't exist, skip
      }
    }
  }

  // Count what was copied
  const sharedCounts: Record<string, number> = {};
  const localCounts: Record<string, number> = {};
  for (const depType of depTypes) {
    sharedCounts[depType] = (resolved.shared[depType] || []).length;
    localCounts[depType] = (resolved.local[depType] || []).length;
  }

  success(`Downloaded to ${targetPath}`);

  const nonZeroShared = Object.entries(sharedCounts).filter(([, v]) => v > 0);
  const nonZeroLocal = Object.entries(localCounts).filter(([, v]) => v > 0);

  if (nonZeroShared.length > 0) {
    const depsStr = nonZeroShared.map(([k, v]) => `${v} ${k}`).join(", ");
    console.log(`  Shared: ${depsStr}`);
  }

  if (nonZeroLocal.length > 0) {
    const depsStr = nonZeroLocal.map(([k, v]) => `${v} ${k}`).join(", ");
    console.log(`  Local: ${depsStr}`);
  }
}

export const getCommand = new Command("get")
  .description("Get project info with all components")
  .argument("<project>", "Project name or path")
  .option("-f, --format <format>", "Output format (tree|json)", "tree")
  .option("-r, --remote <url>", "Git repository URL")
  .option("-d, --download", "Download project with all dependencies")
  .option("-o, --output <dir>", "Output directory for download")
  .action(
    async (
      project: string,
      options: {
        format: string;
        remote?: string;
        download?: boolean;
        output?: string;
      }
    ) => {
      try {
        if (options.remote) {
          // Remote repository support
          warning("Remote repository support is not yet implemented in TypeScript SDK.");
          warning("Use the Python SDK for remote repository features: pip install cldpm");
          process.exit(1);
        }

        const repoRoot = cwd();
        const resolved = await resolveProject(project, repoRoot);

        if (options.format === "json") {
          printProjectJson(resolved);
        } else {
          printProjectTree(resolved);
        }

        // Download if requested
        if (options.download) {
          await downloadLocalProject(resolved, repoRoot, options.output);
        }
      } catch (err) {
        error(`Failed to get project: ${(err as Error).message}`);
        process.exit(1);
      }
    }
  );
