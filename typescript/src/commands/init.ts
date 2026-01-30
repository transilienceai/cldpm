/**
 * cpm init command
 */

import { Command } from "commander";
import { mkdir, writeFile } from "node:fs/promises";
import { join, basename } from "node:path";
import { cwd } from "node:process";
import { createCpmConfig } from "../schemas/index.js";
import { saveCpmConfig, pathExists } from "../core/index.js";
import { success, error, info } from "../utils/index.js";

export const initCommand = new Command("init")
  .description("Initialize a new CPM mono repo")
  .argument("[directory]", "Directory to initialize", ".")
  .option("-n, --name <name>", "Repository name")
  .action(async (directory: string, options: { name?: string }) => {
    try {
      const targetDir =
        directory === "." ? cwd() : join(cwd(), directory);
      const repoName = options.name || basename(targetDir);

      // Check if already initialized
      if (await pathExists(join(targetDir, "cpm.json"))) {
        error("Already initialized: cpm.json exists");
        process.exit(1);
      }

      // Create directory if needed
      if (directory !== ".") {
        await mkdir(targetDir, { recursive: true });
      }

      // Create directory structure
      const dirs = [
        "shared/skills",
        "shared/agents",
        "shared/hooks",
        "shared/rules",
        "projects",
        ".cpm/templates",
      ];

      for (const dir of dirs) {
        await mkdir(join(targetDir, dir), { recursive: true });
      }

      // Create cpm.json
      const config = createCpmConfig(repoName);
      await saveCpmConfig(config, targetDir);

      // Create root CLAUDE.md
      const claudeMd = `# ${repoName}

This is a CPM mono repo containing multiple Claude Code projects.

## Structure

- \`shared/\` - Shared components (skills, agents, hooks, rules)
- \`projects/\` - Individual projects

## Getting Started

\`\`\`bash
# Create a new project
cpm create project my-project

# Create shared components
cpm create skill my-skill
cpm create agent my-agent

# Add components to project
cpm add skill:my-skill --to my-project

# View project info
cpm get my-project
\`\`\`
`;
      await writeFile(join(targetDir, "CLAUDE.md"), claudeMd);

      // Create .gitignore
      const gitignore = `# Dependencies
node_modules/
.venv/

# Build
dist/
build/
*.egg-info/

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Environment
.env
.env.local

# CPM
.cpm/cache/
`;
      await writeFile(join(targetDir, ".gitignore"), gitignore);

      success(`Initialized CPM mono repo: ${repoName}`);
      info(`Created: ${targetDir}`);

      if (directory !== ".") {
        info(`Run: cd ${directory}`);
      }
    } catch (err) {
      error(`Failed to initialize: ${(err as Error).message}`);
      process.exit(1);
    }
  });
