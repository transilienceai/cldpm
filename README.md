# CPM - Claude Project Manager

A CLI tool for managing mono repos with multiple Claude Code projects. Supports shared skills, agents, hooks, and rules across projects without duplication, while also allowing project-specific components.

## Installation

```bash
cd python
pip install -e .
```

## Quick Start

```bash
# Initialize a new mono repo
cpm init my-monorepo
cd my-monorepo

# Create a project
cpm create project my-audit

# Create a shared skill (available to all projects)
mkdir -p shared/skills/common-skill
echo "# Common Skill" > shared/skills/common-skill/SKILL.md

# Add the shared skill to your project
cpm add skill:common-skill --to my-audit

# Create a project-specific (local) skill
mkdir -p projects/my-audit/.claude/skills/local-skill
echo "# Local Skill" > projects/my-audit/.claude/skills/local-skill/SKILL.md

# View project info (shows both shared and local components)
cpm get my-audit

# Clone project with all dependencies
cpm clone my-audit ~/Desktop/standalone-audit

# After git clone, regenerate symlinks
cpm sync --all
```

## Shared vs Local Components

CPM supports two types of components:

| Type | Location | Git Status | Use Case |
|------|----------|------------|----------|
| **Shared** | `shared/{type}/{name}` | Committed, symlinked to projects | Reusable across multiple projects |
| **Local** | `projects/{project}/.claude/{type}/{name}` | Committed directly | Project-specific, not shared |

- **Shared components** are stored in `shared/` and symlinked into projects via `cpm add`
- **Local components** are created directly in a project's `.claude/` directory
- Each `.claude/{type}/` directory has its own `.gitignore` that only ignores symlinks
- Local components are always committed; symlinks are always ignored

## Commands

### `cpm init [directory]`

Initialize a new CPM mono repo or set up an existing repository.

```bash
# Basic usage
cpm init                    # Initialize in current directory
cpm init my-monorepo        # Create and initialize new directory
cpm init --name "My Repo"   # With custom name

# Existing repository
cpm init --existing                              # Initialize without overwriting
cpm init --existing --adopt-projects auto        # Auto-detect and adopt projects
cpm init --existing --adopt-projects "app,api"   # Adopt specific projects

# Custom directories
cpm init --projects-dir src --shared-dir common
```

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--name` | `-n` | Name for the mono repo (default: directory name) |
| `--existing` | `-e` | Initialize in existing directory without overwriting files |
| `--adopt-projects` | `-a` | Adopt existing directories as projects. Use `auto` to detect or comma-separated paths |
| `--projects-dir` | `-p` | Directory for projects (default: `projects`) |
| `--shared-dir` | `-s` | Directory for shared components (default: `shared`) |

---

### `cpm create project <name>`

Create a new project within the mono repo.

```bash
cpm create project my-audit
cpm create project my-audit --description "Security audit project"
cpm create project my-audit --skills skill1,skill2
cpm create project my-audit --skills skill1 --agents agent1
```

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--description` | `-d` | Project description |
| `--skills` | `-s` | Comma-separated list of shared skills to add |
| `--agents` | `-a` | Comma-separated list of shared agents to add |

---

### `cpm add <component> --to <project>`

Add a shared component to a project. Creates a symlink and updates `project.json`.

```bash
# Explicit type
cpm add skill:my-skill --to my-project
cpm add agent:pentester --to my-project
cpm add hook:pre-commit --to my-project
cpm add rule:coding-standards --to my-project

# Auto-detect type (searches shared/ directories)
cpm add my-skill --to my-project
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `COMPONENT` | Component to add. Format: `type:name` or just `name` for auto-detection. Types: `skill`, `agent`, `hook`, `rule` |

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--to` | `-t` | Target project name (required) |

---

### `cpm get <path-or-name>`

Get project info with resolved dependencies. Shows both shared and local components.

```bash
# Local repository
cpm get my-project                    # By project name
cpm get projects/my-project           # By path
cpm get my-project --format json      # JSON output
cpm get my-project --format tree      # Tree view (default)

# Remote repository
cpm get my-project --remote owner/repo
cpm get my-project --remote github.com/owner/repo
cpm get my-project --remote https://github.com/owner/repo
cpm get my-project -r owner/repo --format json

# Download remote repository
cpm get my-project -r owner/repo --download
cpm get my-project -r owner/repo --download --output ./local-copy
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `PATH_OR_NAME` | Project name or path. When using `--remote`, specifies the project within the remote repo |

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--format` | `-f` | Output format: `json` or `tree` (default: `tree`) |
| `--remote` | `-r` | Git repository URL. Supports: `owner/repo`, `github.com/owner/repo`, full HTTPS URLs |
| `--download` | `-d` | Download the repository to current directory (requires `--remote`) |
| `--output` | `-o` | Output directory for download (default: repo name) |

**Environment Variables:**

| Variable | Description |
|----------|-------------|
| `GITHUB_TOKEN` | GitHub token for private repository access |
| `GH_TOKEN` | Alternative GitHub token (used if `GITHUB_TOKEN` not set) |

**Example JSON Output:**

```json
{
  "name": "my-project",
  "path": "/path/to/projects/my-project",
  "config": {
    "name": "my-project",
    "description": "Project description",
    "dependencies": {
      "skills": ["shared-skill"],
      "agents": [],
      "hooks": [],
      "rules": []
    }
  },
  "shared": {
    "skills": [
      {
        "name": "shared-skill",
        "type": "shared",
        "sourcePath": "shared/skills/shared-skill",
        "files": ["SKILL.md"]
      }
    ],
    "agents": [],
    "hooks": [],
    "rules": []
  },
  "local": {
    "skills": [
      {
        "name": "local-skill",
        "type": "local",
        "sourcePath": ".claude/skills/local-skill",
        "files": ["SKILL.md"]
      }
    ],
    "agents": [],
    "hooks": [],
    "rules": []
  }
}
```

---

### `cpm clone <project> <directory>`

Clone a project to a standalone directory with all dependencies resolved and copied.

```bash
cpm clone my-project /path/to/output
cpm clone my-project ./standalone-project
cpm clone my-project ~/Desktop/audit --include-shared
cpm clone my-project ./export --preserve-links
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `PROJECT_NAME` | Name of the project to clone |
| `DIRECTORY` | Target directory for the cloned project |

**Options:**

| Option | Description |
|--------|-------------|
| `--include-shared` | Also copy the full `shared/` directory structure |
| `--preserve-links` | Keep symlinks instead of copying actual files (requires `shared/` to exist at target) |

---

### `cpm sync [project]`

Regenerate symlinks from `project.json` references. Use after `git clone` or when symlinks are broken.

```bash
cpm sync my-project     # Sync single project
cpm sync --all          # Sync all projects
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `PROJECT_NAME` | Name of the project to sync (optional if using `--all`) |

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--all` | `-a` | Sync all projects in the mono repo |

---

## Directory Structure

```
my-monorepo/
├── cpm.json                    # Root configuration
├── CLAUDE.md                   # Root Claude memory
├── .gitignore                  # Standard gitignore (Python, IDE, etc.)
├── shared/                     # Shared components (committed)
│   ├── skills/
│   │   └── shared-skill/
│   │       └── SKILL.md
│   ├── agents/
│   ├── hooks/
│   └── rules/
├── projects/                   # Individual projects
│   └── my-project/
│       ├── project.json        # Project manifest (tracks shared deps)
│       ├── CLAUDE.md           # Project instructions
│       ├── .claude/
│       │   ├── settings.json
│       │   ├── skills/
│       │   │   ├── .gitignore        # Only ignores symlinks!
│       │   │   ├── shared-skill/  -> ../../../../shared/skills/shared-skill (symlink, ignored)
│       │   │   └── local-skill/      # Project-specific (committed)
│       │   │       └── SKILL.md
│       │   ├── agents/
│       │   ├── hooks/
│       │   └── rules/
│       └── outputs/
└── .cpm/                       # CPM internal
    └── templates/
```

## Configuration Files

### `cpm.json` (Root)

```json
{
  "name": "my-monorepo",
  "version": "1.0.0",
  "projectsDir": "projects",
  "sharedDir": "shared"
}
```

### `project.json` (Project)

```json
{
  "name": "my-project",
  "description": "Project description",
  "dependencies": {
    "skills": ["shared-skill"],
    "agents": [],
    "hooks": [],
    "rules": []
  }
}
```

Note: `dependencies` only tracks **shared** components. Local components are discovered automatically from `.claude/` directories.

## How It Works

CPM uses a hybrid approach for managing components:

### Shared Components
- Stored in `shared/` directory (committed to Git)
- Referenced in `project.json` dependencies
- Symlinked to projects via `cpm add` or `cpm sync`
- Symlinks are gitignored (per-directory `.gitignore`)

### Local Components
- Stored directly in `projects/{name}/.claude/{type}/`
- Not tracked in `project.json` (auto-discovered)
- Committed to Git normally
- Project-specific, not shared with other projects

### Git Strategy
Each `.claude/{type}/` directory (skills, agents, hooks, rules) has its own `.gitignore` that **only ignores symlinked shared components**. This means:
- ✅ Local components are committed
- ✅ Shared component symlinks are ignored
- ✅ After `git clone`, run `cpm sync --all` to restore symlinks

### Workflow

1. **Development**:
   - Edit shared components in `shared/` (available to all projects via symlinks)
   - Create local components directly in `projects/{name}/.claude/` (project-specific)
2. **Git operations**: Shared symlinks ignored, local components committed
3. **After clone**: Run `cpm sync --all` to regenerate shared symlinks
4. **Export**: Use `cpm clone` to create standalone projects with all dependencies copied

## Development

```bash
cd python
pip install -e ".[dev]"
pytest
```

## License

MIT
