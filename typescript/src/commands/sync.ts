/**
 * cpm sync command
 */

import { Command } from "commander";
import { cwd } from "node:process";
import {
  listProjects,
  getProjectPath,
  syncProjectLinks,
} from "../core/index.js";
import { success, error, warning, info } from "../utils/index.js";

export const syncCommand = new Command("sync")
  .description("Regenerate symlinks for shared components")
  .argument("[project]", "Project name (optional with --all)")
  .option("-a, --all", "Sync all projects")
  .action(async (project: string | undefined, options: { all: boolean }) => {
    try {
      const repoRoot = cwd();

      if (options.all) {
        // Sync all projects
        const projects = await listProjects(repoRoot);

        if (projects.length === 0) {
          warning("No projects found");
          return;
        }

        for (const proj of projects) {
          const result = await syncProjectLinks(proj.path, repoRoot);

          if (result.created.length > 0) {
            success(`Synced ${proj.name}: ${result.created.length} links`);
          }

          if (result.missing.length > 0) {
            for (const missing of result.missing) {
              warning(`Missing: ${missing}`);
            }
          }
        }

        info(`Synced ${projects.length} projects`);
      } else if (project) {
        // Sync single project
        const projectPath = await getProjectPath(project, repoRoot);

        if (!projectPath) {
          error(`Project not found: ${project}`);
          process.exit(1);
        }

        const result = await syncProjectLinks(projectPath, repoRoot);

        if (result.created.length > 0) {
          success(`Synced ${project}: ${result.created.length} links`);
          for (const created of result.created) {
            info(`  ${created}`);
          }
        } else {
          info("No symlinks to create");
        }

        if (result.missing.length > 0) {
          for (const missing of result.missing) {
            warning(`Missing: ${missing}`);
          }
        }
      } else {
        error("Specify a project name or use --all");
        process.exit(1);
      }
    } catch (err) {
      error(`Failed to sync: ${(err as Error).message}`);
      process.exit(1);
    }
  });
