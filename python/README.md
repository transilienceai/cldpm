# CPM - Claude Project Manager

An SDK and CLI for managing mono repos with multiple Claude Code projects.

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## Overview

CPM enables sharing skills, agents, hooks, and rules across multiple Claude Code projects without duplication. It uses a hybrid linking strategy where references are stored in config files and symlinks are generated locally.

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
cpm create skill logging
cpm create agent code-reviewer

# Add components to project
cpm add skill:logging --to web-app
cpm add agent:code-reviewer --to web-app

# View project with resolved dependencies
cpm get web-app
```

## Architecture

```mermaid
flowchart LR
    subgraph "CPM CLI"
        INIT[cpm init]
        CREATE[cpm create]
        ADD[cpm add]
        GET[cpm get]
        SYNC[cpm sync]
        CLONE[cpm clone]
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
    end

    INIT --> CONFIG
    CREATE --> CONFIG
    ADD --> LINKER
    GET --> RESOLVER
    SYNC --> LINKER
    CLONE --> RESOLVER

    CONFIG --> CPMJSON
    CONFIG --> PROJSON
    RESOLVER --> SHARED
    LINKER --> SHARED
```

## Directory Structure

```
my-monorepo/
├── cpm.json                    # Root configuration
├── CLAUDE.md                   # Root instructions
├── shared/                     # Shared components
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
            ├── skills/         # Symlinks to shared/
            └── agents/
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
```

## Documentation

| Document | Description |
|----------|-------------|
| [CLI Reference](CLI.md) | Complete CLI command reference |
| [SDK Reference](SDK.md) | Programmatic API documentation |
| [Full Docs](https://docs.cpm.dev) | Complete documentation |

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) and [Code of Conduct](CODE_OF_CONDUCT.md).

## Security

For security concerns, please see our [Security Policy](SECURITY.md).

## License

MIT License - see [LICENSE](LICENSE) for details.

---

<p align="center">
  Crafted by <a href="https://transilience.ai"><img src="../docs/logo/transilience.png" alt="Transilience.ai" height="20" style="vertical-align: middle;" /></a> <a href="https://transilience.ai">Transilience.ai</a>
</p>
