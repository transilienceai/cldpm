/**
 * cldpm clone command
 */

import { Command } from "commander";
import { cwd } from "node:process";
import * as path from "node:path";
import * as fs from "node:fs/promises";
import { resolveProject, loadCldpmConfig } from "../core/index.js";
import { error, success } from "../utils/index.js";

/**
 * Copy a directory recursively
 */
async function copyDir(
  src: string,
  dest: string,
  options: { preserveSymlinks?: boolean } = {}
): Promise<void> {
  await fs.mkdir(dest, { recursive: true });
  const entries = await fs.readdir(src, { withFileTypes: true });

  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);

    // Check if it's a symlink using lstat
    const lstat = await fs.lstat(srcPath);

    if (lstat.isSymbolicLink()) {
      if (options.preserveSymlinks) {
        // Preserve symlink
        const linkTarget = await fs.readlink(srcPath);
        await fs.symlink(linkTarget, destPath);
      } else {
        // Resolve symlink and copy the actual content
        const realPath = await fs.realpath(srcPath);
        const stat = await fs.stat(realPath);
        if (stat.isDirectory()) {
          await copyDir(realPath, destPath, options);
        } else {
          await fs.copyFile(realPath, destPath);
        }
      }
    } else if (entry.isDirectory()) {
      await copyDir(srcPath, destPath, options);
    } else {
      await fs.copyFile(srcPath, destPath);
    }
  }
}

/**
 * Print a simple directory tree
 */
async function printDirTree(
  dirPath: string,
  prefix = "",
  maxDepth = 3,
  currentDepth = 0
): Promise<void> {
  if (currentDepth >= maxDepth) return;

  const entries = await fs.readdir(dirPath, { withFileTypes: true });
  const sortedEntries = entries.sort((a, b) => {
    // Directories first, then files
    if (a.isDirectory() && !b.isDirectory()) return -1;
    if (!a.isDirectory() && b.isDirectory()) return 1;
    return a.name.localeCompare(b.name);
  });

  for (let i = 0; i < sortedEntries.length; i++) {
    const entry = sortedEntries[i]!;
    const isLast = i === sortedEntries.length - 1;
    const connector = isLast ? "└── " : "├── ";
    const childPrefix = isLast ? "    " : "│   ";

    console.log(`${prefix}${connector}${entry.name}`);

    if (entry.isDirectory()) {
      await printDirTree(
        path.join(dirPath, entry.name),
        prefix + childPrefix,
        maxDepth,
        currentDepth + 1
      );
    }
  }
}

export const cloneCommand = new Command("clone")
  .description("Clone a project with all dependencies")
  .argument("<project>", "Project name")
  .argument("<directory>", "Target directory")
  .option("--include-shared", "Also copy the full shared/ directory structure")
  .option("--preserve-links", "Keep symlinks instead of copying")
  .action(
    async (
      projectName: string,
      directory: string,
      options: {
        includeShared?: boolean;
        preserveLinks?: boolean;
      }
    ) => {
      try {
        const repoRoot = cwd();

        // Resolve project
        const resolved = await resolveProject(projectName, repoRoot);

        // Get paths
        const sourcePath = resolved.path;
        const targetPath = path.resolve(directory);

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
                      await copyDir(compSrcPath, compDestPath, {
                        preserveSymlinks: options.preserveLinks,
                      });
                    } else {
                      await fs.copyFile(compSrcPath, compDestPath);
                    }
                  }
                }
              } else if (claudeEntry.isFile()) {
                await fs.copyFile(claudeSrcPath, claudeDestPath);
              } else if (claudeEntry.isDirectory()) {
                await copyDir(claudeSrcPath, claudeDestPath, {
                  preserveSymlinks: options.preserveLinks,
                });
              }
            }
          } else if (entry.isDirectory()) {
            await copyDir(srcPath, destPath, {
              preserveSymlinks: options.preserveLinks,
            });
          } else {
            await fs.copyFile(srcPath, destPath);
          }
        }

        // Copy shared dependencies
        const depTypes = ["skills", "agents", "hooks", "rules"] as const;
        const sharedCounts: Record<string, number> = {};

        for (const depType of depTypes) {
          let count = 0;
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
                // Doesn't exist, copy or link
                if (options.preserveLinks) {
                  // Create symlink
                  await fs.symlink(sourceComp, targetComp);
                } else {
                  // Copy actual files
                  const stat = await fs.stat(sourceComp);
                  if (stat.isDirectory()) {
                    await copyDir(sourceComp, targetComp);
                  } else {
                    await fs.copyFile(sourceComp, targetComp);
                  }
                }
                count++;
              }
            } catch {
              // Source doesn't exist, skip
            }
          }
          sharedCounts[depType] = count;
        }

        // Count local components
        const localCounts: Record<string, number> = {};
        for (const depType of depTypes) {
          localCounts[depType] = (resolved.local[depType] || []).length;
        }

        // Optionally copy full shared directory
        if (options.includeShared) {
          const targetShared = path.join(targetPath, "shared");
          await copyDir(sharedDir, targetShared);

          // Also copy cldpm.json
          await fs.copyFile(
            path.join(repoRoot, "cldpm.json"),
            path.join(targetPath, "cldpm.json")
          );
        }

        // Update settings.json if it exists (placeholder for hook path updates)
        const settingsPath = path.join(targetPath, ".claude", "settings.json");
        try {
          await fs.access(settingsPath);
          const content = await fs.readFile(settingsPath, "utf-8");
          const settings = JSON.parse(content);
          // Placeholder for any settings updates
          await fs.writeFile(settingsPath, JSON.stringify(settings, null, 2) + "\n");
        } catch {
          // No settings.json or invalid, skip
        }

        success(`Cloned ${projectName} to ${targetPath}`);

        // Show what was copied
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

        if (options.includeShared) {
          console.log("  Included: full shared/ directory");
        }

        console.log();
        console.log(path.basename(targetPath));
        await printDirTree(targetPath);
      } catch (err) {
        error(`Failed to clone project: ${(err as Error).message}`);
        process.exit(1);
      }
    }
  );
