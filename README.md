# CPM - Claude Project Manager

An SDK and CLI for managing mono repos with multiple Claude Code projects. Supports shared skills, agents, hooks, and rules across projects without duplication.

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## Overview

CPM enables sharing components across multiple Claude Code projects using a hybrid linking strategy. References are stored in config files, and symlinks are generated locally for fast access.

```mermaid
graph TB
    subgraph "Mono Repo"
        CPM[cpm.json]

        subgraph "Shared Components"
            S1[skills/logging]
            S2[skills/code-review]
            A1[agents/debugger]
            H1[hooks/pre-commit]
        end

        subgraph "Projects"
            subgraph "web-app"
                P1[project.json]
                C1[.claude/skills/logging]
                C2[.claude/skills/code-review]
                L1[.claude/skills/local-skill]
            end

            subgraph "api-server"
                P2[project.json]
                C3[.claude/skills/logging]
                C4[.claude/agents/debugger]
            end
        end
    end

    S1 -.->|symlink| C1
    S1 -.->|symlink| C3
    S2 -.->|symlink| C2
    A1 -.->|symlink| C4

    style L1 fill:#6941c6
```

## Installation

```bash
pip install cpm
```

Or with pipx for isolated installation:

```bash
pipx install cpm
```

## Quick Start

```bash
# Initialize a new mono repo
cpm init my-monorepo
cd my-monorepo

# Create a project
cpm create project web-app

# Create shared components
cpm create skill logging -d "Logging utilities"
cpm create agent code-reviewer -d "Code review assistant"

# Add components to project
cpm add skill:logging --to web-app
cpm add agent:code-reviewer --to web-app

# View project with resolved dependencies
cpm get web-app

# After git clone, restore symlinks
cpm sync --all
```

## Architecture

```mermaid
flowchart LR
    subgraph "CPM CLI"
        INIT[init]
        CREATE[create]
        ADD[add]
        REMOVE[remove]
        GET[get]
        SYNC[sync]
        CLONE[clone]
        LINK[link]
    end

    subgraph "Core SDK"
        CONFIG[Config Manager]
        RESOLVER[Dependency Resolver]
        LINKER[Symlink Manager]
    end

    subgraph "Storage"
        CPMJSON[(cpm.json)]
        PROJSON[(project.json)]
        SHARED[(shared/)]
        CLAUDE[(.claude/)]
    end

    INIT --> CONFIG
    CREATE --> CONFIG
    ADD --> LINKER
    REMOVE --> LINKER
    GET --> RESOLVER
    SYNC --> LINKER
    CLONE --> RESOLVER
    LINK --> CONFIG

    CONFIG --> CPMJSON
    CONFIG --> PROJSON
    RESOLVER --> SHARED
    LINKER --> CLAUDE
```

## Shared vs Local Components

CPM supports two types of components:

| Type | Location | Git Status | Use Case |
|------|----------|------------|----------|
| **Shared** | `shared/{type}/{name}` | Committed, symlinked to projects | Reusable across multiple projects |
| **Local** | `projects/{project}/.claude/{type}/{name}` | Committed directly | Project-specific, not shared |

```mermaid
graph LR
    subgraph "Shared"
        SC[shared/skills/logging]
    end

    subgraph "Project A"
        PA[.claude/skills/logging] -->|symlink| SC
        LA[.claude/skills/local-a]
    end

    subgraph "Project B"
        PB[.claude/skills/logging] -->|symlink| SC
        LB[.claude/skills/local-b]
    end

    style LA fill:#6941c6
    style LB fill:#6941c6
```

## Component Dependencies

Shared components can depend on other shared components:

```mermaid
graph TD
    A[advanced-review] --> B[code-review]
    A --> C[security-check]
    B --> D[base-utils]
    C --> D
```

```bash
# Create component with dependencies
cpm create skill advanced-review --skills code-review,security-check

# Link dependencies to existing component
cpm link skill:base-utils --to skill:code-review

# Remove dependencies
cpm unlink skill:base-utils --from skill:code-review
```

## Directory Structure

```
my-monorepo/
├── cpm.json                    # Root configuration
├── CLAUDE.md                   # Root instructions
├── shared/                     # Shared components (committed)
│   ├── skills/
│   │   └── logging/
│   │       ├── SKILL.md
│   │       └── skill.json
│   ├── agents/
│   ├── hooks/
│   └── rules/
└── projects/
    └── web-app/
        ├── project.json        # Dependencies defined here
        ├── CLAUDE.md
        └── .claude/
            ├── skills/
            │   ├── .gitignore        # Ignores symlinks only
            │   ├── logging/ -> symlink (ignored)
            │   └── local-skill/      # Committed
            ├── agents/
            ├── hooks/
            └── rules/
```

## Commands

| Command | Description |
|---------|-------------|
| `cpm init` | Initialize a new mono repo |
| `cpm create project` | Create a new project |
| `cpm create skill/agent/hook/rule` | Create shared components |
| `cpm add` | Add a shared component to a project |
| `cpm remove` | Remove a shared component from a project |
| `cpm link` | Link dependencies between shared components |
| `cpm unlink` | Remove dependencies between shared components |
| `cpm get` | Get project info with resolved dependencies |
| `cpm clone` | Clone a project with all dependencies |
| `cpm sync` | Regenerate symlinks for shared components |

### Remote Repository Support

```bash
# View remote project
cpm get my-project --remote owner/repo

# Download remote project
cpm get my-project -r owner/repo --download --output ./local-copy
```

## Documentation

| Document | Description |
|----------|-------------|
| [Python SDK](python/README.md) | Python SDK and CLI |
| [TypeScript SDK](typescript/README.md) | TypeScript/Node.js SDK and CLI |
| [Full Documentation](docs/) | Complete Mintlify documentation |

## SDKs

### Python

```bash
pip install cpm
```

```python
from cpm.core.config import load_cpm_config, list_projects
from cpm.core.resolver import resolve_project, list_shared_components

# Load configuration
config = load_cpm_config("/path/to/monorepo")

# List all projects
projects = list_projects("/path/to/monorepo")

# Resolve a project with all dependencies
project = resolve_project("my-project", "/path/to/monorepo")
```

### TypeScript

```bash
npm install cpm
```

```typescript
import {
  loadCpmConfig,
  listProjects,
  resolveProject,
  listSharedComponents,
} from "cpm";

// Load configuration
const config = await loadCpmConfig("/path/to/monorepo");

// List all projects
const projects = await listProjects("/path/to/monorepo");

// Resolve a project with all dependencies
const project = await resolveProject("my-project", "/path/to/monorepo");
```

See [SDK Reference](python/SDK.md) for complete API documentation.

## How It Works

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant CPM as CPM CLI
    participant FS as File System
    participant Git as Git

    Dev->>CPM: cpm add skill:logging --to web-app
    CPM->>FS: Update project.json
    CPM->>FS: Create symlink
    CPM->>FS: Update .gitignore

    Dev->>Git: git commit
    Git->>FS: Commit project.json
    Git--xFS: Ignore symlink

    Dev->>Git: git clone (new machine)
    Dev->>CPM: cpm sync --all
    CPM->>FS: Read project.json
    CPM->>FS: Recreate symlinks
```

1. **Source of truth**: `project.json` stores component references
2. **Local optimization**: Symlinks generated via `cpm sync`
3. **Git-friendly**: Per-directory `.gitignore` ignores only symlinks
4. **Cross-platform**: `cpm sync` regenerates symlinks after clone

## Development

```bash
cd python
pip install -e ".[dev]"
pytest
```

## Contributing

Contributions are welcome! See [Contributing Guide](CONTRIBUTING.md) and [Code of Conduct](CODE_OF_CONDUCT.md).

## Security

For security concerns, see [Security Policy](SECURITY.md).

## License

MIT License - see [LICENSE](LICENSE) for details.

---

<p align="center">
  <a href="https://transilience.ai"><img src="docs/logo/transilience.png" alt="Transilience.ai" height="24" /></a>
</p>

<p align="center">
  Crafted by <a href="https://transilience.ai">Transilience.ai</a>
</p>
