# CPM - Claude Project Manager

An SDK and CLI for managing mono repos with multiple Claude Code projects.

## Installation

```bash
pip install cpm
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

## Commands

| Command | Description |
|---------|-------------|
| `cpm init` | Initialize a new mono repo |
| `cpm create` | Create projects or shared components |
| `cpm add` | Add a shared component to a project |
| `cpm remove` | Remove a shared component from a project |
| `cpm link` | Link dependencies between shared components |
| `cpm unlink` | Remove dependencies between shared components |
| `cpm get` | Get project info with resolved dependencies |
| `cpm clone` | Clone a project with all dependencies |
| `cpm sync` | Regenerate symlinks for shared components |

## Programmatic Usage

```python
from cpm.core.config import load_cpm_config, load_project_config, list_projects
from cpm.core.resolver import resolve_project, list_shared_components
from cpm.core.linker import sync_project_links

# Load configuration
config = load_cpm_config("/path/to/monorepo")

# List all projects
projects = list_projects("/path/to/monorepo")

# Resolve a project with all dependencies
project = resolve_project("my-project", "/path/to/monorepo")

# List all shared components
components = list_shared_components("/path/to/monorepo")

# Sync symlinks for a project
sync_project_links(project_path, repo_root)
```

## Documentation

Full documentation available at [docs](../docs).

## License

MIT

---

Crafted by [Transilience.ai](https://transilience.ai)

Authored by [Aman Agarwal](https://github.com/amanagarwal041)
