/**
 * AI rules content for various AI coding assistants.
 */

import { mkdir, writeFile, readFile, appendFile, access } from "node:fs/promises";
import { join, dirname } from "node:path";

// Common section markers for all AI tools
export const CLDPM_SECTION_START = "<!-- CLDPM-SECTION-START -->";
export const CLDPM_SECTION_END = "<!-- CLDPM-SECTION-END -->";

// Legacy marker for backwards compatibility
export const CLDPM_SECTION_MARKER = "<!-- CLDPM-MANAGED-SECTION -->";

/**
 * Get content for .cursor/rules/cldpm.mdc file.
 */
export function getCursorRulesContent(repoName: string, projectsDir: string, sharedDir: string): string {
  return `---
description: CLDPM mono repo management commands
globs:
  - "**/*"
---

${CLDPM_SECTION_START}
# CLDPM - Claude Project Manager

You are working in a CLDPM mono repo. CLDPM manages multiple Claude Code projects with shared components.

## Available Commands

### Initialize & Create
- \`cldpm init [directory]\` - Initialize a new mono repo
- \`cldpm create project <name>\` - Create a new project
- \`cldpm create skill <name>\` - Create a shared skill
- \`cldpm create agent <name>\` - Create a shared agent
- \`cldpm create hook <name>\` - Create a shared hook
- \`cldpm create rule <name>\` - Create a shared rule

### Manage Components
- \`cldpm add <type>:<name> --to <project>\` - Add shared component to project
- \`cldpm remove <type>:<name> --from <project>\` - Remove component from project
- \`cldpm link <type>:<name> --to <type>:<name>\` - Link component dependencies
- \`cldpm unlink <type>:<name> --from <type>:<name>\` - Remove component dependencies

### View & Export
- \`cldpm get <project>\` - View project with resolved dependencies
- \`cldpm get <project> --format json\` - Output as JSON
- \`cldpm clone <project> <directory>\` - Export project with all dependencies

### Maintenance
- \`cldpm sync [project]\` - Regenerate symlinks after git clone
- \`cldpm sync --all\` - Sync all projects

## Directory Structure

\`\`\`
${repoName}/
├── cldpm.json              # Root configuration
├── ${sharedDir}/           # Shared components
│   ├── skills/
│   ├── agents/
│   ├── hooks/
│   └── rules/
└── ${projectsDir}/         # Individual projects
    └── my-project/
        ├── project.json    # Project manifest
        └── .claude/        # Symlinked + local components
\`\`\`

## When User Asks About Projects

If the user asks to:
- "create a new project" → Use \`cldpm create project <name>\`
- "add a skill/agent" → Use \`cldpm add skill:<name> --to <project>\`
- "share a component" → Use \`cldpm create <type> <name>\` then \`cldpm add\`
- "view project structure" → Use \`cldpm get <project>\`
- "export a project" → Use \`cldpm clone <project> <directory>\`

## Configuration Files

- \`cldpm.json\` - Root mono repo config (name, directories)
- \`project.json\` - Project dependencies and metadata
- \`skill.json\` / \`agent.json\` - Component metadata with dependencies
${CLDPM_SECTION_END}
`;
}

/**
 * Get content for .clinerules file.
 */
export function getClineRulesContent(_repoName: string, projectsDir: string, sharedDir: string): string {
  return `${CLDPM_SECTION_START}
# CLDPM - Claude Project Manager

This is a CLDPM mono repo for managing Claude Code projects with shared components.

## CLI Commands

- \`cldpm init\` - Initialize mono repo
- \`cldpm create project <name>\` - Create project
- \`cldpm create skill|agent|hook|rule <name>\` - Create shared component
- \`cldpm add <type>:<name> --to <project>\` - Add component to project
- \`cldpm remove <type>:<name> --from <project>\` - Remove component
- \`cldpm link <type>:<name> --to <type>:<name>\` - Link dependencies
- \`cldpm get <project>\` - View project
- \`cldpm clone <project> <dir>\` - Export project
- \`cldpm sync --all\` - Restore symlinks

## Structure

- \`cldpm.json\` - Root config
- \`${sharedDir}/\` - Shared components (skills, agents, hooks, rules)
- \`${projectsDir}/\` - Individual projects with \`project.json\`
${CLDPM_SECTION_END}
`;
}

/**
 * Get content for .windsurfrules file.
 */
export function getWindsurfRulesContent(repoName: string, projectsDir: string, sharedDir: string): string {
  return `${CLDPM_SECTION_START}
# CLDPM - Claude Project Manager

This is a CLDPM mono repo for managing Claude Code projects with shared components.

## CLI Commands

### Initialize & Create
\`\`\`bash
cldpm init [directory]              # Initialize mono repo
cldpm create project <name>         # Create project
cldpm create skill <name>           # Create shared skill
cldpm create agent <name>           # Create shared agent
\`\`\`

### Manage Components
\`\`\`bash
cldpm add skill:<name> --to <project>      # Add component
cldpm remove skill:<name> --from <project> # Remove component
cldpm link skill:<a> --to skill:<b>        # Link dependencies
\`\`\`

### View & Export
\`\`\`bash
cldpm get <project>                 # View project
cldpm clone <project> <directory>   # Export standalone
cldpm sync --all                    # Restore symlinks
\`\`\`

## Structure

\`\`\`
${repoName}/
├── cldpm.json          # Root config
├── ${sharedDir}/       # Shared components
└── ${projectsDir}/     # Projects
\`\`\`
${CLDPM_SECTION_END}
`;
}

/**
 * Get content for .github/copilot-instructions.md file.
 */
export function getCopilotInstructionsContent(_repoName: string, projectsDir: string, sharedDir: string): string {
  return `${CLDPM_SECTION_START}
# GitHub Copilot Instructions for CLDPM

## Project Overview

This is a CLDPM (Claude Project Manager) mono repo managing multiple Claude Code projects with shared components.

## CLI Commands Reference

\`\`\`bash
# Initialize
cldpm init [directory]

# Create
cldpm create project <name>
cldpm create skill <name>
cldpm create agent <name>

# Add/Remove components
cldpm add <type>:<name> --to <project>
cldpm remove <type>:<name> --from <project>

# Link dependencies
cldpm link <type>:<name> --to <type>:<name>

# View/Export
cldpm get <project> [--format json]
cldpm clone <project> <directory>

# Maintenance
cldpm sync [project | --all]
\`\`\`

## File Structure

- \`cldpm.json\` - Root configuration
- \`project.json\` - Project manifest with dependencies
- \`${sharedDir}/\` - Shared components
- \`${projectsDir}/\` - Individual projects

## When Suggesting Code

- Use \`cldpm\` as the CLI command
- Config file is \`cldpm.json\`
${CLDPM_SECTION_END}
`;
}

/**
 * Get CLDPM section content for CLAUDE.md.
 */
export function getClaudeMdSection(): string {
  return `
${CLDPM_SECTION_START}
## CLDPM Commands

This project is managed by CLDPM. Available commands:

\`\`\`bash
cldpm create project <name>         # Create new project
cldpm create skill <name>           # Create shared skill
cldpm add skill:<name> --to <proj>  # Add component to project
cldpm get <project>                 # View project structure
cldpm clone <project> <dir>         # Export standalone
cldpm sync --all                    # Restore symlinks
\`\`\`
${CLDPM_SECTION_END}
`;
}

/**
 * Get full CLAUDE.md content for new repos.
 */
export function getClaudeMdContent(repoName: string): string {
  return `# ${repoName}

This is a CLDPM mono repo containing multiple Claude Code projects.

## Structure

- \`shared/\` - Shared components (skills, agents, hooks, rules)
- \`projects/\` - Individual projects

## Getting Started

\`\`\`bash
# Create a new project
cldpm create project my-project

# Create shared components
cldpm create skill my-skill
cldpm create agent my-agent

# Add components to project
cldpm add skill:my-skill --to my-project

# View project info
cldpm get my-project
\`\`\`

${CLDPM_SECTION_START}
## CLDPM Commands

This project is managed by CLDPM. Available commands:

\`\`\`bash
cldpm create project <name>         # Create new project
cldpm create skill <name>           # Create shared skill
cldpm add skill:<name> --to <proj>  # Add component to project
cldpm get <project>                 # View project structure
cldpm clone <project> <dir>         # Export standalone
cldpm sync --all                    # Restore symlinks
\`\`\`
${CLDPM_SECTION_END}
`;
}

/**
 * Check if a file exists.
 */
async function fileExists(path: string): Promise<boolean> {
  try {
    await access(path);
    return true;
  } catch {
    return false;
  }
}

/**
 * Replace existing CLDPM section with new content.
 */
function replaceSection(content: string, newSection: string): string {
  const pattern = new RegExp(
    escapeRegex(CLDPM_SECTION_START) + "[\\s\\S]*?" + escapeRegex(CLDPM_SECTION_END),
    "g"
  );
  return content.replace(pattern, newSection.trim());
}

/**
 * Escape special regex characters.
 */
function escapeRegex(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/**
 * Write content to file, update existing section, or append if file exists.
 */
async function writeOrUpdate(
  path: string,
  content: string,
  checkExisting: boolean
): Promise<void> {
  if (checkExisting && await fileExists(path)) {
    const existingContent = await readFile(path, "utf-8");

    if (existingContent.includes(CLDPM_SECTION_START)) {
      // Update existing CLDPM section
      const updated = replaceSection(existingContent, content);
      await writeFile(path, updated);
    } else if (existingContent.includes("CLDPM")) {
      // Has old-style CLDPM content without markers, skip to avoid duplication
      return;
    } else {
      // Append new section
      await appendFile(path, "\n\n" + content);
    }
  } else {
    await mkdir(dirname(path), { recursive: true });
    await writeFile(path, content);
  }
}

/**
 * Create AI rules files for various AI coding assistants.
 *
 * Creates or updates:
 * - .cursor/rules/cldpm.mdc (Cursor IDE - new folder structure)
 * - .clinerules (Cline)
 * - .windsurfrules (Windsurf)
 * - .github/copilot-instructions.md (GitHub Copilot)
 *
 * If files already exist and contain CLDPM sections, updates those sections.
 * Otherwise appends CLDPM section.
 */
export async function createAiRules(
  repoRoot: string,
  repoName: string,
  projectsDir: string = "projects",
  sharedDir: string = "shared",
  existing: boolean = false
): Promise<void> {
  // Create .cursor/rules/cldpm.mdc (Cursor's new folder structure)
  const cursorRulesDir = join(repoRoot, ".cursor", "rules");
  await mkdir(cursorRulesDir, { recursive: true });
  const cursorRulesFile = join(cursorRulesDir, "cldpm.mdc");
  await writeFile(cursorRulesFile, getCursorRulesContent(repoName, projectsDir, sharedDir));

  // Create/update .clinerules
  const clinerrulesPath = join(repoRoot, ".clinerules");
  await writeOrUpdate(
    clinerrulesPath,
    getClineRulesContent(repoName, projectsDir, sharedDir),
    existing
  );

  // Create/update .windsurfrules
  const windsurfrulesPath = join(repoRoot, ".windsurfrules");
  await writeOrUpdate(
    windsurfrulesPath,
    getWindsurfRulesContent(repoName, projectsDir, sharedDir),
    existing
  );

  // Create/update .github/copilot-instructions.md
  const copilotPath = join(repoRoot, ".github", "copilot-instructions.md");
  await writeOrUpdate(
    copilotPath,
    getCopilotInstructionsContent(repoName, projectsDir, sharedDir),
    existing
  );
}

/**
 * Append or update CLDPM section in existing CLAUDE.md.
 */
export async function appendToClaudeMd(claudeMdPath: string): Promise<void> {
  if (!await fileExists(claudeMdPath)) {
    return;
  }

  const content = await readFile(claudeMdPath, "utf-8");
  const newSection = getClaudeMdSection();

  if (content.includes(CLDPM_SECTION_START)) {
    // Update existing section
    const updated = replaceSection(content, newSection);
    await writeFile(claudeMdPath, updated);
  } else if (content.includes(CLDPM_SECTION_MARKER)) {
    // Update legacy section
    const pattern = new RegExp(
      escapeRegex(CLDPM_SECTION_MARKER) + "[\\s\\S]*?" + escapeRegex(CLDPM_SECTION_MARKER),
      "g"
    );
    const updated = content.replace(pattern, newSection.trim());
    await writeFile(claudeMdPath, updated);
  } else {
    // Append new section
    await appendFile(claudeMdPath, newSection);
  }
}
