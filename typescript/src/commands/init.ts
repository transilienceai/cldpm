/**
 * cldpm init command
 */

import { Command } from "commander";
import { mkdir, writeFile } from "node:fs/promises";
import { join, basename } from "node:path";
import { cwd } from "node:process";
import { createCldpmConfig } from "../schemas/index.js";
import { saveCldpmConfig, pathExists } from "../core/index.js";
import { success, error, info } from "../utils/index.js";
import { createAiRules, getClaudeMdContent } from "../ai-rules.js";

export const initCommand = new Command("init")
  .description("Initialize a new CLDPM mono repo")
  .argument("[directory]", "Directory to initialize", ".")
  .option("-n, --name <name>", "Repository name")
  .action(async (directory: string, options: { name?: string }) => {
    try {
      const targetDir =
        directory === "." ? cwd() : join(cwd(), directory);
      const repoName = options.name || basename(targetDir);

      // Check if already initialized
      if (await pathExists(join(targetDir, "cldpm.json"))) {
        error("Already initialized: cldpm.json exists");
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
        ".cldpm/templates",
      ];

      for (const dir of dirs) {
        await mkdir(join(targetDir, dir), { recursive: true });
      }

      // Create cldpm.json
      const config = createCldpmConfig(repoName);
      await saveCldpmConfig(config, targetDir);

      // Create root CLAUDE.md with markers
      await writeFile(join(targetDir, "CLAUDE.md"), getClaudeMdContent(repoName));

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

# CLDPM
.cldpm/cache/
`;
      await writeFile(join(targetDir, ".gitignore"), gitignore);

      // Create AI rules files
      await createAiRules(targetDir, repoName, "projects", "shared", false);

      success(`Initialized CLDPM mono repo: ${repoName}`);
      info(`Created: ${targetDir}`);

      if (directory !== ".") {
        info(`Run: cd ${directory}`);
      }
    } catch (err) {
      error(`Failed to initialize: ${(err as Error).message}`);
      process.exit(1);
    }
  });
