# CLDPM - Claude Project Manager (TypeScript SDK)

An SDK and CLI for managing mono repos with multiple Claude Code projects.

[![npm version](https://img.shields.io/npm/v/cldpm.svg)](https://www.npmjs.com/package/cldpm)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## Overview

CLDPM enables sharing skills, agents, hooks, and rules across multiple Claude Code projects without duplication. It uses a hybrid linking strategy where references are stored in config files and symlinks are generated locally.

## Installation

```bash
npm install cldpm
```

Or globally:

```bash
npm install -g cldpm
```

## CLI Usage

```bash
# Initialize a new mono repo
cldpm init my-monorepo
cd my-monorepo

# Create a project
cldpm create project web-app

# Create shared components
cldpm create skill logging
cldpm create agent code-reviewer

# Add components to project
cldpm add skill:logging --to web-app
cldpm add agent:code-reviewer --to web-app

# View project with resolved dependencies
cldpm get web-app

# Download project with all dependencies
cldpm get web-app --download --output ./temp

# Clone a project to standalone directory
cldpm clone web-app ./standalone

# After git clone, restore symlinks
cldpm sync --all
```

## SDK Usage

```typescript
import {
  loadCldpmConfig,
  resolveProject,
  listProjects,
  listSharedComponents,
  syncProjectLinks,
} from "cldpm";

// Load configuration
const config = await loadCldpmConfig("/path/to/monorepo");
console.log(`Repo: ${config.name}`);

// List all projects
const projects = await listProjects("/path/to/monorepo");
for (const project of projects) {
  console.log(`Project: ${project.name}`);
}

// Resolve a project with all dependencies
const project = await resolveProject("my-project", "/path/to/monorepo");
console.log(`Shared skills: ${project.shared.skills.map(s => s.name)}`);

// List all shared components
const components = await listSharedComponents("/path/to/monorepo");
console.log(`Skills: ${components.skills}`);

// Sync symlinks for a project
const result = await syncProjectLinks(projectPath, repoRoot);
console.log(`Created: ${result.created}`);
```

## Commands

| Command | Description |
|---------|-------------|
| `cldpm init` | Initialize a new mono repo |
| `cldpm create project` | Create a new project |
| `cldpm create skill/agent/hook/rule` | Create shared components |
| `cldpm add` | Add a shared component to a project |
| `cldpm remove` | Remove a shared component from a project |
| `cldpm link` | Link dependencies between shared components |
| `cldpm unlink` | Remove dependencies between shared components |
| `cldpm get` | Get project info with resolved dependencies |
| `cldpm clone` | Clone a project with all dependencies |
| `cldpm sync` | Regenerate symlinks for shared components |
| `cldpm info` | Show CLDPM information banner |

## Documentation

| Document | Description |
|----------|-------------|
| [CLI Reference](CLI.md) | Complete CLI command reference |
| [SDK Reference](SDK.md) | Programmatic API documentation |
| [Contributing](CONTRIBUTING.md) | Contribution guidelines |
| [Security](SECURITY.md) | Security policy |
| [Code of Conduct](CODE_OF_CONDUCT.md) | Community guidelines |

## API Reference

### Schemas

```typescript
import {
  CldpmConfig,
  ProjectConfig,
  ProjectDependencies,
  ComponentMetadata,
  ComponentDependencies,
  ComponentType,
  createCldpmConfig,
  createProjectConfig,
  createComponentMetadata,
  parseComponentRef,
} from "cldpm";
```

### Core Functions

```typescript
import {
  // Config
  loadCldpmConfig,
  saveCldpmConfig,
  loadProjectConfig,
  saveProjectConfig,
  getProjectPath,
  listProjects,
  loadComponentMetadata,
  saveComponentMetadata,

  // Resolver
  resolveProject,
  resolveComponent,
  resolveLocalComponent,
  listSharedComponents,
  resolveComponentDependencies,
  getAllDependenciesForComponent,

  // Linker
  syncProjectLinks,
  addComponentLink,
  removeComponentLink,
  createSymlink,
  removeProjectLinks,
  getLocalComponents,
  getSharedComponents,
} from "cldpm";
```

## Development

```bash
# Install dependencies
npm install

# Build
npm run build

# Run tests
npm test

# Watch mode
npm run dev
```

## License

MIT License - see [LICENSE](LICENSE) for details.

---

<p align="center">
  <a href="https://transilience.ai"><img src="../docs/logo/transilience.png" alt="Transilience.ai" height="24" /></a>
</p>

<p align="center">
  Crafted by <a href="https://transilience.ai">Transilience.ai</a>
</p>
