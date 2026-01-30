"""Implementation of cldpm create command."""

import json
from pathlib import Path
from typing import Optional

import click
from jinja2 import Environment, PackageLoader

from ..schemas import ComponentDependencies, ComponentMetadata, ProjectConfig, ProjectDependencies
from ..core.config import load_cldpm_config, save_project_config
from ..core.linker import sync_project_links
from ..utils.fs import ensure_dir, find_repo_root
from ..utils.output import print_success, print_error, print_dir_tree, console


def parse_dependency_list(deps_str: Optional[str]) -> list[str]:
    """Parse a comma-separated dependency string into a list."""
    if not deps_str:
        return []
    return [d.strip() for d in deps_str.split(",") if d.strip()]


def save_component_metadata(
    metadata: ComponentMetadata,
    component_path: Path,
    component_type: str,
) -> None:
    """Save component metadata to a JSON file.

    Args:
        metadata: The ComponentMetadata to save.
        component_path: Path to the component directory.
        component_type: Type of component (skills, agents, hooks, rules).
    """
    singular_type = component_type.rstrip("s")  # skills -> skill
    metadata_path = component_path / f"{singular_type}.json"

    data = {"name": metadata.name}
    if metadata.description:
        data["description"] = metadata.description

    # Only include dependencies if any exist
    deps = metadata.dependencies
    if deps.skills or deps.agents or deps.hooks or deps.rules:
        data["dependencies"] = {}
        if deps.skills:
            data["dependencies"]["skills"] = deps.skills
        if deps.agents:
            data["dependencies"]["agents"] = deps.agents
        if deps.hooks:
            data["dependencies"]["hooks"] = deps.hooks
        if deps.rules:
            data["dependencies"]["rules"] = deps.rules

    with open(metadata_path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


@click.group()
def create() -> None:
    """Create new projects or components."""
    pass


@create.command()
@click.argument("name")
@click.option("--description", "-d", help="Project description")
@click.option("--skills", "-s", help="Comma-separated list of shared skills to add")
@click.option("--agents", "-a", help="Comma-separated list of shared agents to add")
def project(
    name: str,
    description: Optional[str],
    skills: Optional[str],
    agents: Optional[str],
) -> None:
    """Create a new project in the mono repo.

    Creates a project with the standard structure for Claude Code, including
    directories for both shared (symlinked) and local (project-specific)
    components.

    \b
    Structure created:
      project.json     - Project manifest (tracks shared dependencies)
      CLAUDE.md        - Project instructions
      .claude/         - Components directory
        skills/        - Skills (shared symlinks + local)
        agents/        - Agents (shared symlinks + local)
        hooks/         - Hooks (shared symlinks + local)
        rules/         - Rules (shared symlinks + local)
      outputs/         - Project outputs

    \b
    Examples:
      cldpm create project my-app
      cldpm create project my-app -d "My application"
      cldpm create project my-app --skills skill1,skill2
      cldpm create project my-app -s skill1 -a agent1
    """
    # Find repo root
    repo_root = find_repo_root()
    if repo_root is None:
        print_error("Not in a CLDPM mono repo. Run 'cldpm init' first.")
        raise SystemExit(1)

    # Load config
    cldpm_config = load_cldpm_config(repo_root)

    # Create project directory
    project_path = repo_root / cldpm_config.projects_dir / name

    if project_path.exists():
        print_error(f"Project already exists: {name}")
        raise SystemExit(1)

    ensure_dir(project_path)

    # Parse dependencies
    deps = ProjectDependencies()
    if skills:
        deps.skills = [s.strip() for s in skills.split(",") if s.strip()]
    if agents:
        deps.agents = [a.strip() for a in agents.split(",") if a.strip()]

    # Create project config
    project_config = ProjectConfig(
        name=name,
        description=description,
        dependencies=deps,
    )
    save_project_config(project_config, project_path)

    # Create .claude directory structure
    claude_dir = project_path / ".claude"
    ensure_dir(claude_dir)
    ensure_dir(claude_dir / "skills")
    ensure_dir(claude_dir / "agents")
    ensure_dir(claude_dir / "hooks")
    ensure_dir(claude_dir / "rules")

    # Create settings.json placeholder
    (claude_dir / "settings.json").write_text("{}\n")

    # Create outputs directory
    ensure_dir(project_path / "outputs")

    # Create CLAUDE.md from template
    env = Environment(loader=PackageLoader("cldpm", "templates"))
    template = env.get_template("CLAUDE.md.j2")
    claude_md = template.render(
        project_name=name,
        description=description or "",
    )
    (project_path / "CLAUDE.md").write_text(claude_md)

    print_success(f"Created project: {name}")

    # Sync symlinks if dependencies were specified
    if deps.skills or deps.agents:
        result = sync_project_links(project_path, repo_root)
        if result["created"]:
            console.print(f"  Linked: {', '.join(result['created'])}")
        if result["missing"]:
            console.print(f"  [yellow]Missing:[/yellow] {', '.join(result['missing'])}")

    console.print()
    print_dir_tree(project_path, max_depth=2)


@create.command()
@click.argument("name")
@click.option("--description", "-d", help="Skill description")
@click.option("--skills", "-s", help="Comma-separated list of skill dependencies")
@click.option("--hooks", "-h", "hooks_deps", help="Comma-separated list of hook dependencies")
@click.option("--rules", "-r", help="Comma-separated list of rule dependencies")
def skill(
    name: str,
    description: Optional[str],
    skills: Optional[str],
    hooks_deps: Optional[str],
    rules: Optional[str],
) -> None:
    """Create a new shared skill.

    Creates a skill in the shared/skills/ directory with optional dependencies
    on other shared components.

    \b
    Structure created:
      shared/skills/<name>/
        SKILL.md      - Skill instructions
        skill.json    - Skill metadata and dependencies

    \b
    Examples:
      cldpm create skill code-review
      cldpm create skill code-review -d "Code review assistant"
      cldpm create skill advanced-review --skills base-review,utils
      cldpm create skill full-check -s lint-check -h pre-commit -r security
    """
    _create_component("skills", name, description, skills, None, hooks_deps, rules)


@create.command()
@click.argument("name")
@click.option("--description", "-d", help="Agent description")
@click.option("--skills", "-s", help="Comma-separated list of skill dependencies")
@click.option("--agents", "-a", help="Comma-separated list of agent dependencies")
@click.option("--hooks", "-h", "hooks_deps", help="Comma-separated list of hook dependencies")
@click.option("--rules", "-r", help="Comma-separated list of rule dependencies")
def agent(
    name: str,
    description: Optional[str],
    skills: Optional[str],
    agents: Optional[str],
    hooks_deps: Optional[str],
    rules: Optional[str],
) -> None:
    """Create a new shared agent.

    Creates an agent in the shared/agents/ directory with optional dependencies
    on other shared components.

    \b
    Structure created:
      shared/agents/<name>/
        AGENT.md      - Agent instructions
        agent.json    - Agent metadata and dependencies

    \b
    Examples:
      cldpm create agent debugger
      cldpm create agent debugger -d "Debugging assistant"
      cldpm create agent security-audit --skills vuln-scan,code-review
      cldpm create agent full-audit -s scan -a reviewer -h pre-commit -r security
    """
    _create_component("agents", name, description, skills, agents, hooks_deps, rules)


@create.command()
@click.argument("name")
@click.option("--description", "-d", help="Hook description")
@click.option("--skills", "-s", help="Comma-separated list of skill dependencies")
@click.option("--hooks", "-h", "hooks_deps", help="Comma-separated list of hook dependencies")
@click.option("--rules", "-r", help="Comma-separated list of rule dependencies")
def hook(
    name: str,
    description: Optional[str],
    skills: Optional[str],
    hooks_deps: Optional[str],
    rules: Optional[str],
) -> None:
    """Create a new shared hook.

    Creates a hook in the shared/hooks/ directory with optional dependencies
    on other shared components.

    \b
    Structure created:
      shared/hooks/<name>/
        HOOK.md       - Hook instructions
        hook.json     - Hook metadata and dependencies

    \b
    Examples:
      cldpm create hook pre-commit
      cldpm create hook pre-commit -d "Pre-commit validation"
      cldpm create hook full-validate --skills lint,format --rules style
    """
    _create_component("hooks", name, description, skills, None, hooks_deps, rules)


@create.command()
@click.argument("name")
@click.option("--description", "-d", help="Rule description")
@click.option("--rules", "-r", help="Comma-separated list of rule dependencies")
def rule(
    name: str,
    description: Optional[str],
    rules: Optional[str],
) -> None:
    """Create a new shared rule.

    Creates a rule in the shared/rules/ directory with optional dependencies
    on other rules.

    \b
    Structure created:
      shared/rules/<name>/
        RULE.md       - Rule instructions
        rule.json     - Rule metadata and dependencies

    \b
    Examples:
      cldpm create rule security
      cldpm create rule security -d "Security guidelines"
      cldpm create rule full-compliance --rules security,privacy,logging
    """
    _create_component("rules", name, description, None, None, None, rules)


def _create_component(
    component_type: str,
    name: str,
    description: Optional[str],
    skills: Optional[str],
    agents: Optional[str],
    hooks: Optional[str],
    rules: Optional[str],
) -> None:
    """Create a shared component.

    Args:
        component_type: Type of component (skills, agents, hooks, rules).
        name: Component name.
        description: Component description.
        skills: Comma-separated skill dependencies.
        agents: Comma-separated agent dependencies.
        hooks: Comma-separated hook dependencies.
        rules: Comma-separated rule dependencies.
    """
    # Find repo root
    repo_root = find_repo_root()
    if repo_root is None:
        print_error("Not in a CLDPM mono repo. Run 'cldpm init' first.")
        raise SystemExit(1)

    # Load config
    cldpm_config = load_cldpm_config(repo_root)

    # Create component directory
    component_path = repo_root / cldpm_config.shared_dir / component_type / name

    if component_path.exists():
        print_error(f"Component already exists: {component_type}/{name}")
        raise SystemExit(1)

    ensure_dir(component_path)

    # Parse dependencies
    deps = ComponentDependencies(
        skills=parse_dependency_list(skills),
        agents=parse_dependency_list(agents),
        hooks=parse_dependency_list(hooks),
        rules=parse_dependency_list(rules),
    )

    # Create metadata
    metadata = ComponentMetadata(
        name=name,
        description=description,
        dependencies=deps,
    )
    save_component_metadata(metadata, component_path, component_type)

    # Create content file from template
    singular_type = component_type.rstrip("s")  # skills -> skill
    content_filename = f"{singular_type.upper()}.md"

    env = Environment(loader=PackageLoader("cldpm", "templates"))

    # Try to load component-specific template, fall back to generic
    try:
        template = env.get_template(f"{singular_type}.md.j2")
    except Exception:
        # Use generic template
        template_content = f"""# {name}

{description or f"A shared {singular_type}."}

## Overview

Describe what this {singular_type} does.

## Usage

Explain how to use this {singular_type}.
"""
        (component_path / content_filename).write_text(template_content)
        _print_component_success(component_type, name, deps, component_path)
        return

    content = template.render(
        name=name,
        description=description or "",
    )
    (component_path / content_filename).write_text(content)

    _print_component_success(component_type, name, deps, component_path)


def _print_component_success(
    component_type: str,
    name: str,
    deps: ComponentDependencies,
    component_path: Path,
) -> None:
    """Print success message for component creation."""
    singular_type = component_type.rstrip("s")
    print_success(f"Created {singular_type}: {name}")

    # Show dependencies if any
    all_deps = []
    if deps.skills:
        all_deps.extend([f"skills/{s}" for s in deps.skills])
    if deps.agents:
        all_deps.extend([f"agents/{a}" for a in deps.agents])
    if deps.hooks:
        all_deps.extend([f"hooks/{h}" for h in deps.hooks])
    if deps.rules:
        all_deps.extend([f"rules/{r}" for r in deps.rules])

    if all_deps:
        console.print(f"  Dependencies: {', '.join(all_deps)}")

    console.print(f"  Location: {component_path}")
