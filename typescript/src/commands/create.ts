/**
 * cldpm create command
 */

import { Command } from "commander";
import { mkdir, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { cwd } from "node:process";
import {
  type ComponentType,
  getSingularType,
  createProjectConfig,
  createProjectDependencies,
  createComponentMetadata,
  createComponentDependencies,
} from "../schemas/index.js";
import {
  loadCldpmConfig,
  saveProjectConfig,
  saveComponentMetadata,
  pathExists,
} from "../core/index.js";
import { success, error } from "../utils/index.js";

export const createCommand = new Command("create")
  .description("Create new projects or components");

// cldpm create project
createCommand
  .command("project <name>")
  .description("Create a new project")
  .option("-d, --description <desc>", "Project description")
  .option("-s, --skills <skills>", "Comma-separated skills to add")
  .option("-a, --agents <agents>", "Comma-separated agents to add")
  .action(
    async (
      name: string,
      options: { description?: string; skills?: string; agents?: string }
    ) => {
      try {
        const repoRoot = cwd();
        const config = await loadCldpmConfig(repoRoot);
        // Create project config first to get the kebab-cased id
        const projectConfig = createProjectConfig(name, {
          description: options.description,
          dependencies: createProjectDependencies({
            skills: options.skills?.split(",").map((s) => s.trim()) || [],
            agents: options.agents?.split(",").map((s) => s.trim()) || [],
          }),
        });
        const projectPath = join(repoRoot, config.projectsDir, projectConfig.id);

        if (await pathExists(projectPath)) {
          error(`Project already exists: ${projectConfig.id}`);
          process.exit(1);
        }

        // Create directories
        await mkdir(projectPath, { recursive: true });
        for (const dir of ["skills", "agents", "hooks", "rules"]) {
          await mkdir(join(projectPath, ".claude", dir), { recursive: true });
        }

        await saveProjectConfig(projectConfig, projectPath);

        // Create CLAUDE.md
        const claudeMd = `# ${name}

${options.description || "A Claude Code project."}

## Components

This project uses shared components from the mono repo.
Run \`cldpm get ${projectConfig.id}\` to see all available components.
`;
        await writeFile(join(projectPath, "CLAUDE.md"), claudeMd);

        // Create .claude/settings.json
        const settings = { hooks: {} };
        await writeFile(
          join(projectPath, ".claude", "settings.json"),
          JSON.stringify(settings, null, 2)
        );

        success(`Created project: ${projectConfig.id}`);
      } catch (err) {
        error(`Failed to create project: ${(err as Error).message}`);
        process.exit(1);
      }
    }
  );

// Create component commands
const componentTypes: ComponentType[] = ["skills", "agents", "hooks", "rules"];

for (const compType of componentTypes) {
  const singular = getSingularType(compType);

  createCommand
    .command(`${singular} <name>`)
    .description(`Create a new shared ${singular}`)
    .option("-d, --description <desc>", `${singular} description`)
    .option("-s, --skills <skills>", "Dependent skills (comma-separated)")
    .option("-a, --agents <agents>", "Dependent agents (comma-separated)")
    .option("-h, --hooks <hooks>", "Dependent hooks (comma-separated)")
    .option("-r, --rules <rules>", "Dependent rules (comma-separated)")
    .action(
      async (
        name: string,
        options: {
          description?: string;
          skills?: string;
          agents?: string;
          hooks?: string;
          rules?: string;
        }
      ) => {
        try {
          const repoRoot = cwd();
          const config = await loadCldpmConfig(repoRoot);
          const compPath = join(repoRoot, config.sharedDir, compType, name);

          if (await pathExists(compPath)) {
            error(`${singular} already exists: ${name}`);
            process.exit(1);
          }

          // Create directory
          await mkdir(compPath, { recursive: true });

          // Parse dependencies
          const deps = createComponentDependencies({
            skills: options.skills?.split(",").map((s) => s.trim()) || [],
            agents: options.agents?.split(",").map((s) => s.trim()) || [],
            hooks: options.hooks?.split(",").map((s) => s.trim()) || [],
            rules: options.rules?.split(",").map((s) => s.trim()) || [],
          });

          // Create metadata
          const metadata = createComponentMetadata(name, {
            description: options.description,
            dependencies: deps,
          });
          await saveComponentMetadata(metadata, compType, name, repoRoot);

          // Create main file
          const mainFile = `${singular.toUpperCase()}.md`;
          const content = `# ${name}

${options.description || `A ${singular} component.`}

## Usage

Add this ${singular} to a project:

\`\`\`bash
cldpm add ${singular}:${name} --to <project>
\`\`\`
`;
          await writeFile(join(compPath, mainFile), content);

          success(`Created ${singular}: ${name}`);
        } catch (err) {
          error(`Failed to create ${singular}: ${(err as Error).message}`);
          process.exit(1);
        }
      }
    );
}
