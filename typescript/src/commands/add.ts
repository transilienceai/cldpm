/**
 * cldpm add command
 */

import { Command } from "commander";
import { cwd } from "node:process";
import {
  type ComponentType,
  ComponentTypes,
  parseComponentRef,
} from "../schemas/index.js";
import {
  loadCldpmConfig,
  loadProjectConfig,
  saveProjectConfig,
  getProjectPath,
  pathExists,
  addComponentLink,
  resolveComponentDependencies,
} from "../core/index.js";
import { success, error, warning, info } from "../utils/index.js";
import { join } from "node:path";

export const addCommand = new Command("add")
  .description("Add a shared component to a project")
  .argument("<component>", "Component to add (e.g., skill:my-skill)")
  .requiredOption("-t, --to <project>", "Target project name")
  .option("--no-deps", "Don't install component dependencies")
  .action(
    async (
      component: string,
      options: { to: string; deps: boolean }
    ) => {
      try {
        const repoRoot = cwd();
        const cldpmConfig = await loadCldpmConfig(repoRoot);

        // Parse component reference
        let { type: compType, name: compName } = parseComponentRef(component);

        // Auto-detect type if not specified
        if (!compType) {
          for (const t of ComponentTypes) {
            const compPath = join(
              repoRoot,
              cldpmConfig.sharedDir,
              t,
              compName
            );
            if (await pathExists(compPath)) {
              compType = t;
              break;
            }
          }

          if (!compType) {
            error(`Component not found: ${compName}`);
            process.exit(1);
          }
        }

        // Verify component exists
        const compPath = join(
          repoRoot,
          cldpmConfig.sharedDir,
          compType,
          compName
        );
        if (!(await pathExists(compPath))) {
          error(`Component not found: ${compType}/${compName}`);
          process.exit(1);
        }

        // Get project path
        const projectPath = await getProjectPath(options.to, repoRoot);
        if (!projectPath) {
          error(`Project not found: ${options.to}`);
          process.exit(1);
        }

        // Load project config
        const projectConfig = await loadProjectConfig(projectPath);

        // Check if already added
        if (projectConfig.dependencies[compType].includes(compName)) {
          warning(`Already added: ${compType}/${compName}`);
          return;
        }

        // Collect all components to add (including dependencies)
        const toAdd: Array<[ComponentType, string]> = [[compType, compName]];

        if (options.deps) {
          const deps = await resolveComponentDependencies(
            compType,
            compName,
            repoRoot
          );
          for (const [depType, depName] of deps) {
            if (!projectConfig.dependencies[depType].includes(depName)) {
              toAdd.push([depType, depName]);
            }
          }
        }

        // Add all components
        for (const [type, name] of toAdd) {
          // Update project config
          if (!projectConfig.dependencies[type].includes(name)) {
            projectConfig.dependencies[type].push(name);
          }

          // Create symlink
          const linked = await addComponentLink(
            projectPath,
            type,
            name,
            repoRoot
          );

          if (linked) {
            if (type === compType && name === compName) {
              success(`Added ${type}/${name} to ${options.to}`);
            } else {
              info(`Added dependency: ${type}/${name}`);
            }
          }
        }

        // Save updated config
        await saveProjectConfig(projectConfig, projectPath);
      } catch (err) {
        error(`Failed to add component: ${(err as Error).message}`);
        process.exit(1);
      }
    }
  );
