/**
 * cldpm get command
 */

import { Command } from "commander";
import { cwd } from "node:process";
import * as path from "node:path";
import * as fs from "node:fs/promises";
import * as fsSync from "node:fs";
import { resolveProject, loadCldpmConfig } from "../core/index.js";
import {
  error,
  success,
  warning,
  info,
  printProjectTree,
  printProjectJson,
  getGithubToken,
  parseRepoUrl,
  hasSparseCloneSupport,
  sparseCloneToTemp,
  cloneToTemp,
  cleanupTempDir,
} from "../utils/index.js";
import type { ResolvedProject } from "../core/resolver.js";

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

/**
 * Handle remote get using sparse checkout (optimized).
 */
async function handleRemoteGetSparse(
  projectName: string,
  outputFormat: string,
  remoteUrl: string,
  download: boolean,
  outputDir: string | undefined,
  repoUrl: string,
  branch: string | null,
  token: string | undefined
): Promise<void> {
  let tempConfig: string | null = null;
  let tempDir: string | null = null;

  try {
    // Phase 1: Get config files only (tiny download)
    info(`Fetching project config from ${repoUrl}...`);
    const configPaths = ["cldpm.json"];
    tempConfig = await sparseCloneToTemp(repoUrl, configPaths, branch ?? undefined, token);

    // Parse cldpm.json to get directories
    const cldpmJsonPath = path.join(tempConfig, "cldpm.json");
    try {
      await fs.access(cldpmJsonPath);
    } catch {
      error("Remote repository is not a CLDPM mono repo (no cldpm.json found)");
      process.exit(1);
    }

    const cldpmConfigContent = await fs.readFile(cldpmJsonPath, "utf-8");
    const cldpmConfig = JSON.parse(cldpmConfigContent);

    const projectsDir = cldpmConfig.projectsDir || "projects";
    const sharedDir = cldpmConfig.sharedDir || "shared";
    const projectPath = `${projectsDir}/${projectName}`;

    await cleanupTempDir(tempConfig);
    tempConfig = null;

    // Phase 2: Get project.json to find dependencies
    info("Fetching project metadata...");
    const projectConfigPaths = [`${projectPath}/project.json`];
    const tempProject = await sparseCloneToTemp(repoUrl, projectConfigPaths, branch ?? undefined, token);

    const projectJsonPath = path.join(tempProject, projectPath, "project.json");
    try {
      await fs.access(projectJsonPath);
    } catch {
      await cleanupTempDir(tempProject);
      error(`Project not found: ${projectName}`);
      process.exit(1);
    }

    const projectConfigContent = await fs.readFile(projectJsonPath, "utf-8");
    const projectConfig = JSON.parse(projectConfigContent);

    await cleanupTempDir(tempProject);

    // Build path list for final sparse clone
    const allPaths = [projectPath];
    const dependencies = projectConfig.dependencies || {};
    const depTypes = ["skills", "agents", "hooks", "rules"] as const;

    for (const depType of depTypes) {
      const deps = dependencies[depType] || [];
      for (const depName of deps) {
        allPaths.push(`${sharedDir}/${depType}/${depName}`);
      }
    }

    // Phase 3: Download everything needed
    info("Downloading project and dependencies...");
    tempDir = await sparseCloneToTemp(repoUrl, allPaths, branch ?? undefined, token);

    // Build result for display
    const result = buildSparseResult(
      tempDir,
      projectName,
      projectPath,
      sharedDir,
      projectConfig,
      dependencies
    );

    // Output the result
    if (outputFormat === "json") {
      printProjectJson(result);
    } else {
      printProjectTree(result);
      console.log(`\nSource: ${remoteUrl}`);
    }

    // Download if requested
    if (download) {
      await downloadSparseProject(
        tempDir,
        outputDir,
        projectName,
        projectPath,
        sharedDir,
        dependencies,
        repoUrl
      );
      await cleanupTempDir(tempDir);
      tempDir = null;
    }
  } catch (err) {
    const errMsg = (err as Error & { stderr?: string }).stderr || (err as Error).message;
    if (errMsg.includes("Authentication failed") || errMsg.includes("could not read")) {
      error("Authentication failed. Set GITHUB_TOKEN or GH_TOKEN environment variable.");
    } else {
      error(`Git error: ${errMsg}`);
    }
    process.exit(1);
  } finally {
    if (tempConfig) {
      await cleanupTempDir(tempConfig);
    }
    if (tempDir && !download) {
      await cleanupTempDir(tempDir);
    }
  }
}

/**
 * Handle remote get using full clone (fallback for old Git versions).
 */
async function handleRemoteGetFull(
  projectName: string,
  outputFormat: string,
  remoteUrl: string,
  download: boolean,
  outputDir: string | undefined,
  repoUrl: string,
  branch: string | null,
  token: string | undefined
): Promise<void> {
  let tempDir: string | null = null;

  try {
    // Clone to temporary directory
    info(`Cloning ${repoUrl}...`);
    tempDir = await cloneToTemp(repoUrl, branch ?? undefined, token);

    // Check if it's a valid CLDPM repo
    const cldpmJsonPath = path.join(tempDir, "cldpm.json");
    try {
      await fs.access(cldpmJsonPath);
    } catch {
      error("Remote repository is not a CLDPM mono repo (no cldpm.json found)");
      process.exit(1);
    }

    // Resolve the project
    const result = await resolveProject(projectName, tempDir);

    // Add remote info to result
    (result as ResolvedProject & { remote?: object }).remote = {
      url: remoteUrl,
      repoUrl,
      branch,
    };

    // Output the result
    if (outputFormat === "json") {
      printProjectJson(result);
    } else {
      printProjectTree(result);
      console.log(`\nSource: ${remoteUrl}`);
    }

    // Download if requested
    if (download) {
      await downloadRemoteProject(result, tempDir, outputDir, repoUrl);
    }
  } catch (err) {
    const errMsg = (err as Error & { stderr?: string }).stderr || (err as Error).message;
    if (errMsg.includes("Authentication failed") || errMsg.includes("could not read")) {
      error("Authentication failed. Set GITHUB_TOKEN or GH_TOKEN environment variable.");
    } else {
      error(`Git error: ${errMsg}`);
    }
    process.exit(1);
  } finally {
    if (tempDir && !download) {
      await cleanupTempDir(tempDir);
    }
  }
}

/**
 * Build the result dictionary for sparse clone output.
 */
function buildSparseResult(
  tempDir: string,
  projectName: string,
  projectPath: string,
  sharedDir: string,
  projectConfig: Record<string, unknown>,
  dependencies: Record<string, string[]>
): ResolvedProject {
  const sourceProject = path.join(tempDir, projectPath);
  const depTypes = ["skills", "agents", "hooks", "rules"] as const;

  // Build a minimal ProjectConfig from the raw config
  const config = {
    name: (projectConfig.name as string) || projectName,
    description: projectConfig.description as string | undefined,
    dependencies: {
      skills: (dependencies.skills || []) as string[],
      agents: (dependencies.agents || []) as string[],
      hooks: (dependencies.hooks || []) as string[],
      rules: (dependencies.rules || []) as string[],
    },
  };

  const result: ResolvedProject = {
    name: projectName,
    path: sourceProject,
    config,
    shared: { skills: [], agents: [], hooks: [], rules: [] },
    local: { skills: [], agents: [], hooks: [], rules: [] },
  };

  // Build shared components info
  for (const depType of depTypes) {
    const deps = dependencies[depType] || [];
    for (const depName of deps) {
      const sourceComp = path.join(tempDir, sharedDir, depType, depName);
      // Get list of files in the component
      let files: string[] = [];
      try {
        const stat = fsSync.statSync(sourceComp);
        if (stat.isDirectory()) {
          files = fsSync.readdirSync(sourceComp).filter((f: string) => {
            const fstat = fsSync.statSync(path.join(sourceComp, f));
            return fstat.isFile();
          });
        }
      } catch {
        // Component doesn't exist
      }
      // Build a minimal ResolvedComponent
      result.shared[depType].push({
        name: depName,
        type: "shared",
        sourcePath: `${sharedDir}/${depType}/${depName}`,
        files,
      });
    }
  }

  // Build local components info
  const claudeDir = path.join(sourceProject, ".claude");
  for (const depType of depTypes) {
    const typeDir = path.join(claudeDir, depType);
    try {
      const items = fsSync.readdirSync(typeDir, { withFileTypes: true });
      for (const item of items) {
        if (item.name !== ".gitignore" && !fsSync.lstatSync(path.join(typeDir, item.name)).isSymbolicLink()) {
          // Get list of files in the component
          let files: string[] = [];
          const itemPath = path.join(typeDir, item.name);
          try {
            if (fsSync.statSync(itemPath).isDirectory()) {
              files = fsSync.readdirSync(itemPath).filter((f: string) => {
                return fsSync.statSync(path.join(itemPath, f)).isFile();
              });
            }
          } catch {
            // Ignore
          }
          result.local[depType].push({
            name: item.name,
            type: "local",
            sourcePath: `.claude/${depType}/${item.name}`,
            files,
          });
        }
      }
    } catch {
      // Directory doesn't exist
    }
  }

  return result;
}

/**
 * Download a project from sparse clone with proper file placement.
 */
async function downloadSparseProject(
  tempDir: string,
  outputDir: string | undefined,
  projectName: string,
  projectPath: string,
  sharedDir: string,
  dependencies: Record<string, string[]>,
  repoUrl: string
): Promise<void> {
  // Determine target directory
  const target = outputDir ? path.resolve(outputDir) : path.join(cwd(), projectName);

  // Check if target exists
  try {
    await fs.access(target);
    error(`Target directory already exists: ${target}`);
    process.exit(1);
  } catch {
    // Directory doesn't exist, which is what we want
  }

  const sourceProject = path.join(tempDir, projectPath);

  // Create target directory
  await fs.mkdir(target, { recursive: true });

  // Copy project files
  const entries = await fs.readdir(sourceProject, { withFileTypes: true });
  for (const entry of entries) {
    const srcPath = path.join(sourceProject, entry.name);
    const destPath = path.join(target, entry.name);

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

  // Place shared components directly in .claude/<type>/<name>/
  const depTypes = ["skills", "agents", "hooks", "rules"] as const;
  for (const depType of depTypes) {
    const deps = dependencies[depType] || [];
    for (const depName of deps) {
      const sourceComp = path.join(tempDir, sharedDir, depType, depName);
      const targetComp = path.join(target, ".claude", depType, depName);

      try {
        await fs.access(sourceComp);
        try {
          await fs.access(targetComp);
          // Already exists, skip
        } catch {
          // Doesn't exist, copy
          await fs.mkdir(path.dirname(targetComp), { recursive: true });
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
    sharedCounts[depType] = (dependencies[depType] || []).length;
    localCounts[depType] = 0;
  }

  // Count local components
  const claudeDir = path.join(sourceProject, ".claude");
  for (const depType of depTypes) {
    const typeDir = path.join(claudeDir, depType);
    try {
      const items = await fs.readdir(typeDir, { withFileTypes: true });
      for (const item of items) {
        if (item.name !== ".gitignore") {
          const itemPath = path.join(typeDir, item.name);
          const lstat = await fs.lstat(itemPath);
          if (!lstat.isSymbolicLink()) {
            localCounts[depType] = (localCounts[depType] ?? 0) + 1;
          }
        }
      }
    } catch {
      // Directory doesn't exist
    }
  }

  success(`Downloaded to ${target}`);
  console.log(`  Source: ${repoUrl}`);

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

/**
 * Download a remote project with all dependencies resolved (full clone fallback).
 */
async function downloadRemoteProject(
  resolved: ResolvedProject,
  tempDir: string,
  outputDir: string | undefined,
  repoUrl: string
): Promise<void> {
  const projectName = resolved.name;

  // Determine target directory
  const target = outputDir ? path.resolve(outputDir) : path.join(cwd(), projectName);

  // Check if target exists
  try {
    await fs.access(target);
    error(`Target directory already exists: ${target}`);
    process.exit(1);
  } catch {
    // Directory doesn't exist, which is what we want
  }

  // Load CLDPM config for shared directory path
  const cldpmConfig = await loadCldpmConfig(tempDir);
  const sharedDirPath = path.join(tempDir, cldpmConfig.sharedDir);
  const sourcePath = resolved.path;

  // Create target directory
  await fs.mkdir(target, { recursive: true });

  // Copy project files
  const entries = await fs.readdir(sourcePath, { withFileTypes: true });
  for (const entry of entries) {
    const srcPath = path.join(sourcePath, entry.name);
    const destPath = path.join(target, entry.name);

    if (entry.name === ".claude") {
      await fs.mkdir(destPath, { recursive: true });
      const claudeEntries = await fs.readdir(srcPath, { withFileTypes: true });

      for (const claudeEntry of claudeEntries) {
        const claudeSrcPath = path.join(srcPath, claudeEntry.name);
        const claudeDestPath = path.join(destPath, claudeEntry.name);

        if (["skills", "agents", "hooks", "rules"].includes(claudeEntry.name)) {
          await fs.mkdir(claudeDestPath, { recursive: true });
          const compEntries = await fs.readdir(claudeSrcPath, { withFileTypes: true });
          for (const compEntry of compEntries) {
            if (compEntry.name === ".gitignore") continue;

            const compSrcPath = path.join(claudeSrcPath, compEntry.name);
            const compDestPath = path.join(claudeDestPath, compEntry.name);

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

  // Copy shared dependencies
  const depTypes = ["skills", "agents", "hooks", "rules"] as const;
  for (const depType of depTypes) {
    const components = resolved.shared[depType] || [];
    for (const component of components) {
      const compName = component.name;
      const sourceComp = path.join(sharedDirPath, depType, compName);
      const targetComp = path.join(target, ".claude", depType, compName);

      try {
        await fs.access(sourceComp);
        try {
          await fs.access(targetComp);
          // Already exists, skip
        } catch {
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

  // Clean up temp directory
  await cleanupTempDir(tempDir);

  success(`Downloaded to ${target}`);
  console.log(`  Source: ${repoUrl}`);
}

export const getCommand = new Command("get")
  .description("Get project info with all components")
  .argument("<project>", "Project name or path")
  .option("-f, --format <format>", "Output format (tree|json)", "tree")
  .option("-r, --remote <url>", "Git repository URL")
  .option("-b, --branch <name>", "Git branch name (use when branch contains slashes)")
  .option("-d, --download", "Download project with all dependencies")
  .option("-o, --output <dir>", "Output directory for download")
  .action(
    async (
      project: string,
      options: {
        format: string;
        remote?: string;
        branch?: string;
        download?: boolean;
        output?: string;
      }
    ) => {
      try {
        if (options.remote) {
          // Get GitHub token
          const token = getGithubToken();
          if (!token) {
            warning("No GITHUB_TOKEN or GH_TOKEN found. Private repos may not be accessible.");
          }

          // Parse the remote URL
          const { repoUrl, branch: urlBranch } = parseRepoUrl(options.remote);

          // Use explicit branch if provided, otherwise use branch from URL
          const branch = options.branch ?? urlBranch;

          // Check if sparse clone is supported
          const useSparse = await hasSparseCloneSupport();

          if (useSparse) {
            await handleRemoteGetSparse(
              project,
              options.format,
              options.remote,
              options.download ?? false,
              options.output,
              repoUrl,
              branch,
              token
            );
          } else {
            await handleRemoteGetFull(
              project,
              options.format,
              options.remote,
              options.download ?? false,
              options.output,
              repoUrl,
              branch,
              token
            );
          }
          return;
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
