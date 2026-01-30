/**
 * cldpm remove command
 */

import { Command } from "commander";
import { cwd } from "node:process";
import { parseComponentRef } from "../schemas/index.js";
import {
  loadProjectConfig,
  saveProjectConfig,
  getProjectPath,
  removeComponentLink,
} from "../core/index.js";
import { success, error, warning } from "../utils/index.js";

export const removeCommand = new Command("remove")
  .description("Remove a shared component from a project")
  .argument("<component>", "Component to remove (e.g., skill:my-skill)")
  .requiredOption("-f, --from <project>", "Source project name")
  .option("--force", "Remove without confirmation")
  .action(
    async (
      component: string,
      options: { from: string; force: boolean }
    ) => {
      try {
        const repoRoot = cwd();

        // Parse component reference
        const { type: compType, name: compName } = parseComponentRef(component);

        if (!compType) {
          error("Component type required (e.g., skill:my-skill)");
          process.exit(1);
        }

        // Get project path
        const projectPath = await getProjectPath(options.from, repoRoot);
        if (!projectPath) {
          error(`Project not found: ${options.from}`);
          process.exit(1);
        }

        // Load project config
        const projectConfig = await loadProjectConfig(projectPath);

        // Check if component exists in project
        const deps = projectConfig.dependencies[compType];
        const index = deps.indexOf(compName);

        if (index === -1) {
          warning(`Component not in project: ${compType}/${compName}`);
          return;
        }

        // Remove from config
        deps.splice(index, 1);

        // Remove symlink
        await removeComponentLink(projectPath, compType, compName);

        // Save updated config
        await saveProjectConfig(projectConfig, projectPath);

        success(`Removed ${compType}/${compName} from ${options.from}`);
      } catch (err) {
        error(`Failed to remove component: ${(err as Error).message}`);
        process.exit(1);
      }
    }
  );
