"""Implementation of cpm add command."""

from pathlib import Path
from typing import Optional

import click

from ..core.config import (
    get_project_path,
    load_cpm_config,
    load_project_config,
    save_project_config,
)
from ..core.linker import add_component_link
from ..core.resolver import get_all_dependencies_for_component
from ..utils.fs import find_repo_root
from ..utils.output import console, print_error, print_success, print_warning


def parse_component(component: str, repo_root: Path) -> tuple[str, str]:
    """Parse a component specification into type and name.

    Args:
        component: Component spec like "skill:my-skill" or just "my-skill".
        repo_root: Path to the repo root for auto-detection.

    Returns:
        Tuple of (component_type, component_name).

    Raises:
        ValueError: If component type cannot be determined.
    """
    # Check for explicit type prefix
    if ":" in component:
        comp_type, comp_name = component.split(":", 1)
        # Normalize type to plural form
        type_map = {
            "skill": "skills",
            "skills": "skills",
            "agent": "agents",
            "agents": "agents",
            "hook": "hooks",
            "hooks": "hooks",
            "rule": "rules",
            "rules": "rules",
        }
        if comp_type not in type_map:
            raise ValueError(f"Unknown component type: {comp_type}")
        return type_map[comp_type], comp_name

    # Auto-detect type by searching shared directories
    cpm_config = load_cpm_config(repo_root)
    shared_dir = repo_root / cpm_config.shared_dir

    for comp_type in ["skills", "agents", "hooks", "rules"]:
        if (shared_dir / comp_type / component).exists():
            return comp_type, component

    raise ValueError(
        f"Component '{component}' not found. Use 'type:name' format or ensure it exists in shared/."
    )


def add_single_component(
    comp_type: str,
    comp_name: str,
    project_path: Path,
    repo_root: Path,
    is_dependency: bool = False,
) -> bool:
    """Add a single component to a project.

    Args:
        comp_type: Component type (skills, agents, hooks, rules).
        comp_name: Component name.
        project_path: Path to the project directory.
        repo_root: Path to the repo root.
        is_dependency: Whether this is being added as a dependency.

    Returns:
        True if added successfully, False if already exists or failed.
    """
    cpm_config = load_cpm_config(repo_root)
    shared_dir = repo_root / cpm_config.shared_dir
    component_path = shared_dir / comp_type / comp_name

    if not component_path.exists():
        if is_dependency:
            console.print(f"  [yellow]![/yellow] {comp_type}/{comp_name} (dependency not found)")
        return False

    # Load project config
    project_config = load_project_config(project_path)
    deps_list = getattr(project_config.dependencies, comp_type)

    # Check if already added
    if comp_name in deps_list:
        return False

    # Add to dependencies
    deps_list.append(comp_name)
    save_project_config(project_config, project_path)

    # Create symlink
    if add_component_link(project_path, comp_type, comp_name, repo_root):
        if is_dependency:
            console.print(f"  [green]✓[/green] {comp_type}/{comp_name} (dependency)")
        return True
    else:
        if is_dependency:
            console.print(f"  [yellow]![/yellow] {comp_type}/{comp_name} (symlink failed)")
        return False


@click.command()
@click.argument("component")
@click.option("--to", "-t", "project_name", required=True, help="Target project name")
@click.option("--no-deps", is_flag=True, help="Skip installing component dependencies")
def add(component: str, project_name: str, no_deps: bool) -> None:
    """Add a shared component to a project.

    Creates a symlink from the project's .claude/ directory to the shared
    component, and updates project.json dependencies. The symlink is
    automatically gitignored; only the reference in project.json is committed.

    Components can have dependencies on other components. By default, all
    dependencies are also added. Use --no-deps to skip dependencies.

    \b
    COMPONENT format:
      type:name    - Explicit type (skill, agent, hook, rule)
      name         - Auto-detect type from shared/ directory

    \b
    Note: For project-specific (local) components, create them directly in
    projects/<name>/.claude/<type>/ - no 'cpm add' needed.

    \b
    Examples:
      cpm add skill:my-skill --to my-project
      cpm add agent:pentester --to my-project
      cpm add hook:pre-commit -t my-project
      cpm add my-skill --to my-project          # Auto-detect type
      cpm add agent:security --to my-project --no-deps
    """
    # Find repo root
    repo_root = find_repo_root()
    if repo_root is None:
        print_error("Not in a CPM mono repo. Run 'cpm init' first.")
        raise SystemExit(1)

    # Get project path
    project_path = get_project_path(project_name, repo_root)
    if project_path is None:
        print_error(f"Project not found: {project_name}")
        raise SystemExit(1)

    # Parse component
    try:
        comp_type, comp_name = parse_component(component, repo_root)
    except ValueError as e:
        print_error(str(e))
        raise SystemExit(1)

    # Check if component exists
    cpm_config = load_cpm_config(repo_root)
    shared_dir = repo_root / cpm_config.shared_dir
    component_path = shared_dir / comp_type / comp_name

    if not component_path.exists():
        print_error(f"Component not found: {comp_type}/{comp_name}")
        raise SystemExit(1)

    # Load project config to check if already added
    project_config = load_project_config(project_path)
    deps_list = getattr(project_config.dependencies, comp_type)

    if comp_name in deps_list:
        print_warning(f"Component already in project: {comp_type}/{comp_name}")
        return

    # Add the main component
    deps_list.append(comp_name)
    save_project_config(project_config, project_path)

    # Create symlink
    if add_component_link(project_path, comp_type, comp_name, repo_root):
        print_success(f"Added {comp_type}/{comp_name} to {project_name}")
    else:
        print_warning(f"Added to config but failed to create symlink for {comp_type}/{comp_name}")

    # Add dependencies if not skipped
    if not no_deps:
        all_deps = get_all_dependencies_for_component(comp_type, comp_name, repo_root)
        deps_added = False

        for dep_type, dep_names in all_deps.items():
            for dep_name in dep_names:
                if add_single_component(
                    dep_type, dep_name, project_path, repo_root, is_dependency=True
                ):
                    deps_added = True

        if not deps_added and any(all_deps.values()):
            # Dependencies exist but were already added
            pass
