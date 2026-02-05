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
description: CLDPM mono repo - ALWAYS use cldpm CLI for project management
globs:
  - "**/*"
alwaysApply: true
---

{CLDPM_SECTION_START}
# CLDPM - Claude Project Manager

This is a CLDPM-managed mono repo. **You MUST use `cldpm` CLI commands** to manage projects, skills, agents, hooks, and rules. Do NOT manually create or modify project structures.

## IMPORTANT: Execute These Commands

When the user asks you to perform any of these actions, **run the corresponding command in the terminal**:

### Creating Things
| User Request | Command to Execute |
|--------------|-------------------|
| "create a project" / "new project" | `cldpm create project <name>` |
| "create a skill" / "new skill" | `cldpm create skill <name>` |
| "create an agent" / "new agent" | `cldpm create agent <name>` |
| "create a hook" | `cldpm create hook <name>` |
| "create a rule" | `cldpm create rule <name>` |

### Managing Components
| User Request | Command to Execute |
|--------------|-------------------|
| "add skill to project" / "use skill in" | `cldpm add skill:<name> --to <project>` |
| "add agent to project" | `cldpm add agent:<name> --to <project>` |
| "remove skill from project" | `cldpm remove skill:<name> --from <project>` |
| "link skills" / "skill depends on" | `cldpm link skill:<dep> --to skill:<target>` |

### Viewing & Exporting
| User Request | Command to Execute |
|--------------|-------------------|
| "show project" / "project info" / "what's in project" | `cldpm get <project>` |
| "list projects" | `cldpm get <project> --format json` |
| "export project" / "standalone copy" | `cldpm get <project> --download -o <directory>` |
| "fix symlinks" / "restore links" | `cldpm sync --all` |

## Directory Structure

```
{repo_name}/
├── cldpm.json              # Root configuration (DO NOT edit manually)
├── {shared_dir}/           # Shared components
│   ├── skills/
│   ├── agents/
│   ├── hooks/
│   └── rules/
└── {projects_dir}/         # Individual projects
    └── <project>/
        ├── project.json    # Project manifest (managed by cldpm)
        └── .claude/        # Symlinked + local components
```

## Installation

**BEFORE running any `cldpm` command**, check if it's installed and install if needed:

1. **Check if `cldpm` exists**: Run `which cldpm` or `cldpm --version`
2. **If not found, detect environment and install**:
   ```bash
   # Check for Python environment (pyproject.toml, requirements.txt, setup.py, or python/python3 command)
   if [ -f "pyproject.toml" ] || [ -f "requirements.txt" ] || [ -f "setup.py" ] || command -v python &> /dev/null || command -v python3 &> /dev/null; then
     pip install cldpm || pip3 install cldpm
   # Check for Node.js/TypeScript environment (package.json, tsconfig.json, or node/npm command)
   elif [ -f "package.json" ] || [ -f "tsconfig.json" ] || command -v node &> /dev/null || command -v npm &> /dev/null; then
     npm install -g cldpm
   # Default to Python if neither detected
   else
     pip install cldpm || pip3 install cldpm
   fi
   ```

**Or manually install**:
- Python: `pip install cldpm` or `pip3 install cldpm`
- Node.js: `npm install -g cldpm`

## Rules

1. **ALWAYS** use `cldpm` commands - never manually create project.json or skill.json files
2. **ALWAYS** run `cldpm sync --all` after git pull/clone
3. **NEVER** manually create symlinks - use `cldpm add` instead
4. When creating components, add `-d "description"` for documentation
{CLDPM_SECTION_END}
"""


def get_clinerules_content(_repo_name: str, projects_dir: str, shared_dir: str) -> str:
    """Get content for .clinerules file."""
    return f"""{CLDPM_SECTION_START}
# CLDPM Mono Repo - USE CLI COMMANDS

This repo uses CLDPM. **Execute these commands** for project management:

## Execute These Commands (don't do manually)

```bash
# Create things
cldpm create project <name>           # New project
cldpm create skill <name>             # New shared skill
cldpm create agent <name>             # New shared agent

# Add components to projects
cldpm add skill:<name> --to <project>
cldpm add agent:<name> --to <project>

# View projects
cldpm get <project>                   # Show project structure
cldpm get <project> --format json     # JSON output

# Maintenance
cldpm sync --all                      # Restore symlinks after git clone
```

## Action Mapping

- "create project" → RUN `cldpm create project <name>`
- "add skill" → RUN `cldpm add skill:<name> --to <project>`
- "show project" → RUN `cldpm get <project>`
- "export" → RUN `cldpm get <project> --download -o <dir>`

## Installation

**BEFORE running `cldpm` commands**, check if installed and install if needed:

1. **Check**: `which cldpm` or `cldpm --version`
2. **If missing, detect environment and install**:
   - **Python detected** (pyproject.toml, requirements.txt, setup.py, or python/python3 exists): `pip install cldpm` or `pip3 install cldpm`
   - **Node.js/TypeScript detected** (package.json, tsconfig.json, or node/npm exists): `npm install -g cldpm`
   - **Default**: `pip install cldpm` or `pip3 install cldpm`

## Structure

- `{shared_dir}/` - Shared components (use `cldpm create`)
- `{projects_dir}/` - Projects (use `cldpm create project`)
{CLDPM_SECTION_END}
"""


def get_windsurfrules_content(repo_name: str, projects_dir: str, shared_dir: str) -> str:
    """Get content for .windsurfrules file."""
    return f"""{CLDPM_SECTION_START}
# CLDPM Mono Repo - EXECUTE CLI COMMANDS

**IMPORTANT**: This repo is managed by CLDPM. Always execute `cldpm` commands instead of manually editing files.

## Command Reference - EXECUTE THESE

### When user wants to create:
```bash
cldpm create project <name>     # Execute for: "create project", "new project"
cldpm create skill <name>       # Execute for: "create skill", "new skill"
cldpm create agent <name>       # Execute for: "create agent", "new agent"
```

### When user wants to add/remove:
```bash
cldpm add skill:<name> --to <project>      # Execute for: "add skill to"
cldpm remove skill:<name> --from <project> # Execute for: "remove skill from"
```

### When user wants to view/export:
```bash
cldpm get <project>                  # Execute for: "show project", "project info"
cldpm get <project> --download -o <directory>  # Execute for: "export", "standalone"
cldpm sync --all                     # Execute for: "fix links", "after clone"
```

## Structure

```
{repo_name}/
├── cldpm.json          # Config (managed by cldpm)
├── {shared_dir}/       # Shared components
└── {projects_dir}/     # Projects
```

## Installation

**BEFORE running `cldpm` commands**, check if installed and install if needed:

1. **Check**: `which cldpm` or `cldpm --version`
2. **If missing, detect environment and install**:
   - **Python detected** (pyproject.toml, requirements.txt, setup.py, or python/python3 exists): `pip install cldpm` or `pip3 install cldpm`
   - **Node.js/TypeScript detected** (package.json, tsconfig.json, or node/npm exists): `npm install -g cldpm`
   - **Default**: `pip install cldpm` or `pip3 install cldpm`

## Rules
- NEVER manually edit project.json or skill.json
- ALWAYS use cldpm commands
{CLDPM_SECTION_END}
"""


def get_copilot_instructions_content(_repo_name: str, projects_dir: str, shared_dir: str) -> str:
    """Get content for .github/copilot-instructions.md file."""
    return f"""{CLDPM_SECTION_START}
# CLDPM Mono Repo - GitHub Copilot Instructions

This repository uses **CLDPM (Claude Project Manager)**. When suggesting code or actions, use the `cldpm` CLI.

## EXECUTE These Commands

When the user asks for project management tasks, suggest and execute these commands:

| User Intent | Command to Execute |
|-------------|-------------------|
| Create a new project | `cldpm create project <name> -d "description"` |
| Create a shared skill | `cldpm create skill <name> -d "description"` |
| Create a shared agent | `cldpm create agent <name> -d "description"` |
| Add skill to project | `cldpm add skill:<name> --to <project>` |
| Remove skill from project | `cldpm remove skill:<name> --from <project>` |
| View project structure | `cldpm get <project>` |
| Export standalone project | `cldpm get <project> --download -o <directory>` |
| Restore symlinks | `cldpm sync --all` |

## File Structure

- `cldpm.json` - Root config (DO NOT manually edit)
- `project.json` - Project manifest (managed by cldpm)
- `{shared_dir}/` - Shared components
- `{projects_dir}/` - Individual projects

## Installation

**BEFORE running `cldpm` commands**, check if installed and install if needed:

1. **Check**: `which cldpm` or `cldpm --version`
2. **If missing, detect environment and install**:
   - **Node.js/TypeScript detected** (node/npm exists): `npm install -g cldpm`
   - **Python detected** (python/python3 exists): `pip install cldpm` or `pip3 install cldpm`
   - **Priority**: First try Node.js/TypeScript, then Python

## Important Rules

1. **Use `cldpm` commands** - don't manually create/edit config files
2. **Run `cldpm sync --all`** after cloning the repository
3. **Use `cldpm add`** to add components - don't manually create symlinks
{CLDPM_SECTION_END}
"""


def get_claude_md_section() -> str:
    """Get CLDPM section content for CLAUDE.md."""
    return f"""
{CLDPM_SECTION_START}
## CLDPM Commands - EXECUTE THESE

This project uses CLDPM. **Run these commands** for project management:

```bash
# Creating
cldpm create project <name>         # Run for: "create project"
cldpm create skill <name>           # Run for: "create skill"

# Managing
cldpm add skill:<name> --to <proj>  # Run for: "add skill to project"
cldpm remove skill:<name> --from <proj>  # Run for: "remove skill"

# Viewing
cldpm get <project>                 # Run for: "show project", "project info"
cldpm get <project> --download      # Run for: "export project"
cldpm sync --all                    # Run for: "fix symlinks", "after clone"
```

**IMPORTANT**: Always use `cldpm` commands. Never manually edit project.json or create symlinks.

## Installation

**BEFORE running `cldpm` commands**, check if installed and install if needed:

1. **Check**: `which cldpm` or `cldpm --version`
2. **If missing, detect environment and install**:
   - **Python detected** (pyproject.toml, requirements.txt, setup.py, or python/python3 exists): `pip install cldpm` or `pip3 install cldpm`
   - **Node.js/TypeScript detected** (package.json, tsconfig.json, or node/npm exists): `npm install -g cldpm`
   - **Default**: `pip install cldpm` or `pip3 install cldpm`
{CLDPM_SECTION_END}
"""


def get_claude_md_content(repo_name: str) -> str:
    """Get full CLAUDE.md content for new repos."""
    return f"""# {repo_name}

This is a CLDPM-managed mono repo for Claude Code projects.

## Structure

- `shared/` - Shared components (skills, agents, hooks, rules)
- `projects/` - Individual projects

## Quick Start - EXECUTE THESE COMMANDS

```bash
# Create a new project
cldpm create project my-project -d "My awesome project"

# Create shared components
cldpm create skill my-skill -d "Reusable skill"
cldpm create agent my-agent -d "Shared agent"

# Add components to project
cldpm add skill:my-skill --to my-project

# View project info
cldpm get my-project

# After git clone, restore symlinks
cldpm sync --all
```

{CLDPM_SECTION_START}
## CLDPM Commands - EXECUTE THESE

This project uses CLDPM. **Run these commands** for project management:

```bash
# Creating
cldpm create project <name>         # Run for: "create project"
cldpm create skill <name>           # Run for: "create skill"

# Managing
cldpm add skill:<name> --to <proj>  # Run for: "add skill to project"
cldpm remove skill:<name> --from <proj>  # Run for: "remove skill"

# Viewing
cldpm get <project>                 # Run for: "show project", "project info"
cldpm get <project> --download      # Run for: "export project"
cldpm sync --all                    # Run for: "fix symlinks", "after clone"
```

**IMPORTANT**: Always use `cldpm` commands. Never manually edit project.json or create symlinks.

## Installation

**BEFORE running `cldpm` commands**, check if installed and install if needed:

1. **Check**: `which cldpm` or `cldpm --version`
2. **If missing, detect environment and install**:
   - **Python detected** (pyproject.toml, requirements.txt, setup.py, or python/python3 exists): `pip install cldpm` or `pip3 install cldpm`
   - **Node.js/TypeScript detected** (package.json, tsconfig.json, or node/npm exists): `npm install -g cldpm`
   - **Default**: `pip install cldpm` or `pip3 install cldpm`
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
