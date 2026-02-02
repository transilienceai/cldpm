"""AI rules content for various AI coding assistants."""

import re
from pathlib import Path


# Common section markers for all AI tools
CLDPM_SECTION_START = "<!-- CLDPM-SECTION-START -->"
CLDPM_SECTION_END = "<!-- CLDPM-SECTION-END -->"

# Legacy marker for backwards compatibility
CLDPM_SECTION_MARKER = "<!-- CLDPM-MANAGED-SECTION -->"


def get_cursorrules_content(repo_name: str, projects_dir: str, shared_dir: str) -> str:
    """Get content for .cursor/rules/cldpm.mdc file."""
    return f"""---
description: CLDPM mono repo management commands
globs:
  - "**/*"
---

{CLDPM_SECTION_START}
# CLDPM - Claude Project Manager

You are working in a CLDPM mono repo. CLDPM manages multiple Claude Code projects with shared components.

## Available Commands

### Initialize & Create
- `cldpm init [directory]` - Initialize a new mono repo
- `cldpm create project <name>` - Create a new project
- `cldpm create skill <name>` - Create a shared skill
- `cldpm create agent <name>` - Create a shared agent
- `cldpm create hook <name>` - Create a shared hook
- `cldpm create rule <name>` - Create a shared rule

### Manage Components
- `cldpm add <type>:<name> --to <project>` - Add shared component to project
- `cldpm remove <type>:<name> --from <project>` - Remove component from project
- `cldpm link <type>:<name> --to <type>:<name>` - Link component dependencies
- `cldpm unlink <type>:<name> --from <type>:<name>` - Remove component dependencies

### View & Export
- `cldpm get <project>` - View project with resolved dependencies
- `cldpm get <project> --format json` - Output as JSON
- `cldpm clone <project> <directory>` - Export project with all dependencies

### Maintenance
- `cldpm sync [project]` - Regenerate symlinks after git clone
- `cldpm sync --all` - Sync all projects

## Directory Structure

```
{repo_name}/
├── cldpm.json              # Root configuration
├── {shared_dir}/           # Shared components
│   ├── skills/
│   ├── agents/
│   ├── hooks/
│   └── rules/
└── {projects_dir}/         # Individual projects
    └── my-project/
        ├── project.json    # Project manifest
        └── .claude/        # Symlinked + local components
```

## When User Asks About Projects

If the user asks to:
- "create a new project" → Use `cldpm create project <name>`
- "add a skill/agent" → Use `cldpm add skill:<name> --to <project>`
- "share a component" → Use `cldpm create <type> <name>` then `cldpm add`
- "view project structure" → Use `cldpm get <project>`
- "export a project" → Use `cldpm clone <project> <directory>`

## Configuration Files

- `cldpm.json` - Root mono repo config (name, directories)
- `project.json` - Project dependencies and metadata
- `skill.json` / `agent.json` - Component metadata with dependencies
{CLDPM_SECTION_END}
"""


def get_clinerules_content(_repo_name: str, projects_dir: str, shared_dir: str) -> str:
    """Get content for .clinerules file."""
    return f"""{CLDPM_SECTION_START}
# CLDPM - Claude Project Manager

This is a CLDPM mono repo for managing Claude Code projects with shared components.

## CLI Commands

- `cldpm init` - Initialize mono repo
- `cldpm create project <name>` - Create project
- `cldpm create skill|agent|hook|rule <name>` - Create shared component
- `cldpm add <type>:<name> --to <project>` - Add component to project
- `cldpm remove <type>:<name> --from <project>` - Remove component
- `cldpm link <type>:<name> --to <type>:<name>` - Link dependencies
- `cldpm get <project>` - View project
- `cldpm clone <project> <dir>` - Export project
- `cldpm sync --all` - Restore symlinks

## Structure

- `cldpm.json` - Root config
- `{shared_dir}/` - Shared components (skills, agents, hooks, rules)
- `{projects_dir}/` - Individual projects with `project.json`
{CLDPM_SECTION_END}
"""


def get_windsurfrules_content(repo_name: str, projects_dir: str, shared_dir: str) -> str:
    """Get content for .windsurfrules file."""
    return f"""{CLDPM_SECTION_START}
# CLDPM - Claude Project Manager

This is a CLDPM mono repo for managing Claude Code projects with shared components.

## CLI Commands

### Initialize & Create
```bash
cldpm init [directory]              # Initialize mono repo
cldpm create project <name>         # Create project
cldpm create skill <name>           # Create shared skill
cldpm create agent <name>           # Create shared agent
```

### Manage Components
```bash
cldpm add skill:<name> --to <project>      # Add component
cldpm remove skill:<name> --from <project> # Remove component
cldpm link skill:<a> --to skill:<b>        # Link dependencies
```

### View & Export
```bash
cldpm get <project>                 # View project
cldpm clone <project> <directory>   # Export standalone
cldpm sync --all                    # Restore symlinks
```

## Structure

```
{repo_name}/
├── cldpm.json          # Root config
├── {shared_dir}/       # Shared components
└── {projects_dir}/     # Projects
```
{CLDPM_SECTION_END}
"""


def get_copilot_instructions_content(_repo_name: str, projects_dir: str, shared_dir: str) -> str:
    """Get content for .github/copilot-instructions.md file."""
    return f"""{CLDPM_SECTION_START}
# GitHub Copilot Instructions for CLDPM

## Project Overview

This is a CLDPM (Claude Project Manager) mono repo managing multiple Claude Code projects with shared components.

## CLI Commands Reference

```bash
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
```

## File Structure

- `cldpm.json` - Root configuration
- `project.json` - Project manifest with dependencies
- `{shared_dir}/` - Shared components
- `{projects_dir}/` - Individual projects

## When Suggesting Code

- Use `cldpm` as the CLI command
- Config file is `cldpm.json`
{CLDPM_SECTION_END}
"""


def get_claude_md_section() -> str:
    """Get CLDPM section content for CLAUDE.md."""
    return f"""
{CLDPM_SECTION_START}
## CLDPM Commands

This project is managed by CLDPM. Available commands:

```bash
cldpm create project <name>         # Create new project
cldpm create skill <name>           # Create shared skill
cldpm add skill:<name> --to <proj>  # Add component to project
cldpm get <project>                 # View project structure
cldpm clone <project> <dir>         # Export standalone
cldpm sync --all                    # Restore symlinks
```
{CLDPM_SECTION_END}
"""


def get_claude_md_content(repo_name: str) -> str:
    """Get full CLAUDE.md content for new repos."""
    return f"""# {repo_name}

This is a CLDPM mono repo containing multiple Claude Code projects.

## Structure

- `shared/` - Shared components (skills, agents, hooks, rules)
- `projects/` - Individual projects

## Getting Started

```bash
# Create a new project
cldpm create project my-project

# Create shared components
cldpm create skill my-skill
cldpm create agent my-agent

# Add components to project
cldpm add skill:my-skill --to my-project

# View project info
cldpm get my-project
```

{CLDPM_SECTION_START}
## CLDPM Commands

This project is managed by CLDPM. Available commands:

```bash
cldpm create project <name>         # Create new project
cldpm create skill <name>           # Create shared skill
cldpm add skill:<name> --to <proj>  # Add component to project
cldpm get <project>                 # View project structure
cldpm clone <project> <dir>         # Export standalone
cldpm sync --all                    # Restore symlinks
```
{CLDPM_SECTION_END}
"""


def create_ai_rules(
    repo_root: Path,
    repo_name: str,
    projects_dir: str,
    shared_dir: str,
    existing: bool = False,
) -> None:
    """Create AI rules files for various AI coding assistants.

    Creates or updates:
    - .cursor/rules/cldpm.mdc (Cursor IDE - new folder structure)
    - .clinerules (Cline)
    - .windsurfrules (Windsurf)
    - .github/copilot-instructions.md (GitHub Copilot)

    If files already exist and contain CLDPM sections, updates those sections.
    Otherwise appends CLDPM section.
    """
    # Create .cursor/rules/cldpm.mdc (Cursor's new folder structure)
    cursor_rules_dir = repo_root / ".cursor" / "rules"
    cursor_rules_dir.mkdir(parents=True, exist_ok=True)
    cursor_rules_file = cursor_rules_dir / "cldpm.mdc"
    cursor_rules_file.write_text(get_cursorrules_content(repo_name, projects_dir, shared_dir))

    # Create/update .clinerules
    clinerules_path = repo_root / ".clinerules"
    _write_or_update(
        clinerules_path,
        get_clinerules_content(repo_name, projects_dir, shared_dir),
        existing,
    )

    # Create/update .windsurfrules
    windsurfrules_path = repo_root / ".windsurfrules"
    _write_or_update(
        windsurfrules_path,
        get_windsurfrules_content(repo_name, projects_dir, shared_dir),
        existing,
    )

    # Create/update .github/copilot-instructions.md
    github_dir = repo_root / ".github"
    github_dir.mkdir(parents=True, exist_ok=True)
    copilot_path = github_dir / "copilot-instructions.md"
    _write_or_update(
        copilot_path,
        get_copilot_instructions_content(repo_name, projects_dir, shared_dir),
        existing,
    )


def append_to_claude_md(claude_md_path: Path) -> None:
    """Append or update CLDPM section in existing CLAUDE.md."""
    if not claude_md_path.exists():
        return

    content = claude_md_path.read_text()
    new_section = get_claude_md_section()

    # Check for existing CLDPM section (new or legacy markers)
    if CLDPM_SECTION_START in content:
        # Update existing section
        updated = _replace_section(content, new_section)
        claude_md_path.write_text(updated)
    elif CLDPM_SECTION_MARKER in content:
        # Update legacy section
        pattern = re.compile(
            re.escape(CLDPM_SECTION_MARKER) + r".*?" + re.escape(CLDPM_SECTION_MARKER),
            re.DOTALL
        )
        updated = pattern.sub(new_section.strip(), content)
        claude_md_path.write_text(updated)
    else:
        # Append new section
        with open(claude_md_path, "a") as f:
            f.write(new_section)


def _replace_section(content: str, new_section: str) -> str:
    """Replace existing CLDPM section with new content."""
    pattern = re.compile(
        re.escape(CLDPM_SECTION_START) + r".*?" + re.escape(CLDPM_SECTION_END),
        re.DOTALL
    )
    return pattern.sub(new_section.strip(), content)


def _write_or_update(
    path: Path,
    content: str,
    check_existing: bool,
) -> None:
    """Write content to file, update existing section, or append if file exists."""
    if check_existing and path.exists():
        existing_content = path.read_text()

        if CLDPM_SECTION_START in existing_content:
            # Update existing CLDPM section
            updated = _replace_section(existing_content, content)
            path.write_text(updated)
        elif "CLDPM" in existing_content:
            # Has old-style CLDPM content without markers, skip to avoid duplication
            return
        else:
            # Append new section
            with open(path, "a") as f:
                f.write("\n\n")
                f.write(content)
    else:
        path.write_text(content)
