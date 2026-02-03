/**
 * cldpm init command
 */

import { Command } from "commander";
import { mkdir, writeFile, readFile, appendFile, readdir } from "node:fs/promises";
import { join, basename } from "node:path";
import { cwd } from "node:process";
import { createCldpmConfig } from "../schemas/index.js";
import { saveCldpmConfig, pathExists } from "../core/index.js";
import { success, error, info, warning } from "../utils/index.js";
import { createAiRules, getClaudeMdContent, appendToClaudeMd, CLDPM_SECTION_START, CLDPM_SECTION_END } from "../ai-rules.js";

export const initCommand = new Command("init")
  .description("Initialize a new CLDPM mono repo")
  .argument("[directory]", "Directory to initialize", ".")
  .option("-n, --name <name>", "Repository name")
  .option("-e, --existing", "Initialize in an existing directory without overwriting files")
  .action(async (directory: string, options: { name?: string; existing?: boolean }) => {
    try {
      const targetDir =
        directory === "." ? cwd() : join(cwd(), directory);
      const repoName = options.name || basename(targetDir);
      const existing = options.existing || false;

      // Check if already initialized
      if (await pathExists(join(targetDir, "cldpm.json"))) {
        if (existing) {
          warning(`CLDPM repo already exists at ${targetDir}, updating...`);
        } else {
          error("Already initialized: cldpm.json exists");
          process.exit(1);
        }
      }

      // Check if directory exists and has content (for non-existing mode)
      if (!existing && await pathExists(targetDir)) {
        try {
          const entries = await readdir(targetDir);
          if (entries.length > 0) {
            error(
              `Directory ${targetDir} is not empty. Use --existing to initialize an existing repo.`
            );
            process.exit(1);
          }
        } catch {
          // Directory doesn't exist or can't be read, which is fine
        }
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

      // Create root CLAUDE.md (only if it doesn't exist or not in existing mode)
      const claudeMdPath = join(targetDir, "CLAUDE.md");
      if (!existing || !(await pathExists(claudeMdPath))) {
        await writeFile(claudeMdPath, getClaudeMdContent(repoName));
      }

      // Create or update .gitignore
      const gitignorePath = join(targetDir, ".gitignore");
      const cldpmGitignoreSection = `
# ${CLDPM_SECTION_START}
# CLDPM - Claude Project Manager
.cldpm/cache/

# CLDPM Note: Shared component symlinks are managed per-directory
# Each .claude/{skills,agents,hooks,rules}/ has its own .gitignore
# that only ignores symlinked shared components.
# Project-specific components in those directories ARE committed.
# ${CLDPM_SECTION_END}
`;

      if (await pathExists(gitignorePath)) {
        // Check if CLDPM section already exists
        const existingContent = await readFile(gitignorePath, "utf-8");
        if (!existingContent.includes("CLDPM")) {
          // Append CLDPM section
          await appendFile(gitignorePath, cldpmGitignoreSection);
        }
      } else {
        // Create new .gitignore with common patterns + CLDPM section
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
${cldpmGitignoreSection}`;
        await writeFile(gitignorePath, gitignore);
      }

      // Create AI rules files
      await createAiRules(targetDir, repoName, "projects", "shared", existing);

      // Append CLDPM section to CLAUDE.md if it exists and doesn't have it
      if (existing) {
        await appendToClaudeMd(claudeMdPath);
      }

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
