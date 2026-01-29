"""Implementation of cpm remove command."""

from pathlib import Path

import click

from ..core.config import (
    get_project_path,
    load_cpm_config,
    load_project_config,
    save_project_config,
)
from ..core.linker import update_component_gitignore
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
    if ":" in component:
        comp_type, comp_name = component.split(":", 1)
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

    # Auto-detect from project dependencies
    raise ValueError(
        f"Component '{component}' type not specified. Use 'type:name' format."
    )


def get_component_dependents(
    comp_type: str,
    comp_name: str,
    project_path: Path,
    repo_root: Path,
) -> list[tuple[str, str]]:
    """Find components in the project that depend on the given component.

    Args:
        comp_type: Component type being removed.
        comp_name: Component name being removed.
        project_path: Path to the project directory.
        repo_root: Path to the repo root.

    Returns:
        List of (comp_type, comp_name) tuples that depend on this component.
    """
    project_config = load_project_config(project_path)
    dependents = []

    # Check all components in the project
    for check_type in ["skills", "agents", "hooks", "rules"]:
        check_list = getattr(project_config.dependencies, check_type)
        for check_name in check_list:
            if check_type == comp_type and check_name == comp_name:
                continue

            # Get dependencies of this component
            deps = get_all_dependencies_for_component(check_type, check_name, repo_root)
            dep_list = deps.get(comp_type, [])

            if comp_name in dep_list:
                dependents.append((check_type, check_name))

    return dependents


def find_orphaned_dependencies(
    comp_type: str,
    comp_name: str,
    project_path: Path,
    repo_root: Path,
) -> list[tuple[str, str]]:
    """Find dependencies that would become orphaned after removal.

    A dependency is orphaned if no other component in the project uses it.

    Args:
        comp_type: Component type being removed.
        comp_name: Component name being removed.
        project_path: Path to the project directory.
        repo_root: Path to the repo root.

    Returns:
        List of (comp_type, comp_name) tuples that would be orphaned.
    """
    project_config = load_project_config(project_path)

    # Get dependencies of the component being removed
    removed_deps = get_all_dependencies_for_component(comp_type, comp_name, repo_root)

    orphaned = []

    for dep_type, dep_names in removed_deps.items():
        for dep_name in dep_names:
            # Check if any other component in the project uses this dependency
            is_used = False

            for check_type in ["skills", "agents", "hooks", "rules"]:
                check_list = getattr(project_config.dependencies, check_type)
                for check_name in check_list:
                    # Skip the component being removed
                    if check_type == comp_type and check_name == comp_name:
                        continue

                    # Skip the dependency itself (it's a direct dependency)
                    if check_type == dep_type and check_name == dep_name:
                        is_used = True
                        break

                    # Check if this component depends on the dependency
                    check_deps = get_all_dependencies_for_component(
                        check_type, check_name, repo_root
                    )
                    if dep_name in check_deps.get(dep_type, []):
                        is_used = True
                        break

                if is_used:
                    break

            if not is_used:
                orphaned.append((dep_type, dep_name))

    return orphaned


def remove_single_component(
    comp_type: str,
    comp_name: str,
    project_path: Path,
    repo_root: Path,
) -> bool:
    """Remove a single component from a project.

    Args:
        comp_type: Component type (skills, agents, hooks, rules).
        comp_name: Component name.
        project_path: Path to the project directory.
        repo_root: Path to the repo root.

    Returns:
        True if removed successfully, False otherwise.
    """
    project_config = load_project_config(project_path)
    deps_list = getattr(project_config.dependencies, comp_type)

    if comp_name not in deps_list:
        return False

    # Remove from dependencies
    deps_list.remove(comp_name)
    save_project_config(project_config, project_path)

    # Remove symlink
    remove_component_link(project_path, comp_type, comp_name)

    # Update gitignore
    component_dir = project_path / ".claude" / comp_type
    if component_dir.exists():
        # Get remaining symlinks
        remaining_symlinks = [
            item.name
            for item in component_dir.iterdir()
            if item.is_symlink()
        ]
        update_component_gitignore(component_dir, remaining_symlinks)

    return True


def remove_component_link(project_path: Path, comp_type: str, comp_name: str) -> None:
    """Remove a component symlink from a project.

    Args:
        project_path: Path to the project directory.
        comp_type: Component type (skills, agents, hooks, rules).
        comp_name: Component name.
    """
    link_path = project_path / ".claude" / comp_type / comp_name
    if link_path.is_symlink():
        link_path.unlink()


@click.command()
@click.argument("component")
@click.option("--from", "-f", "project_name", required=True, help="Target project name")
@click.option("--keep-deps", is_flag=True, help="Keep orphaned dependencies")
@click.option("--force", is_flag=True, help="Remove even if other components depend on it")
def remove(component: str, project_name: str, keep_deps: bool, force: bool) -> None:
    """Remove a shared component from a project.

    Removes the component from project.json and deletes the symlink.
    By default, also offers to remove orphaned dependencies.

    \b
    COMPONENT format:
      type:name    - Explicit type (skill, agent, hook, rule)

    \b
    Examples:
      cpm remove skill:my-skill --from my-project
      cpm remove agent:pentester -f my-project
      cpm remove skill:common --from my-project --keep-deps
      cpm remove skill:shared --from my-project --force
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

    # Check if component is in project
    project_config = load_project_config(project_path)
    deps_list = getattr(project_config.dependencies, comp_type)

    if comp_name not in deps_list:
        print_error(f"Component not in project: {comp_type}/{comp_name}")
        raise SystemExit(1)

    # Check for dependents
    dependents = get_component_dependents(comp_type, comp_name, project_path, repo_root)
    if dependents and not force:
        print_error(f"Cannot remove {comp_type}/{comp_name}: other components depend on it")
        for dep_type, dep_name in dependents:
            console.print(f"  - {dep_type}/{dep_name}")
        console.print("\nUse --force to remove anyway.")
        raise SystemExit(1)

    # Find orphaned dependencies
    orphaned = []
    if not keep_deps:
        orphaned = find_orphaned_dependencies(comp_type, comp_name, project_path, repo_root)

    # Remove the main component
    if remove_single_component(comp_type, comp_name, project_path, repo_root):
        print_success(f"Removed {comp_type}/{comp_name} from {project_name}")
    else:
        print_error(f"Failed to remove {comp_type}/{comp_name}")
        raise SystemExit(1)

    # Handle orphaned dependencies
    if orphaned:
        console.print("\n[dim]Orphaned dependencies:[/dim]")
        for dep_type, dep_name in orphaned:
            console.print(f"  - {dep_type}/{dep_name}")

        if click.confirm("\nRemove orphaned dependencies?", default=True):
            for dep_type, dep_name in orphaned:
                if remove_single_component(dep_type, dep_name, project_path, repo_root):
                    console.print(f"  [green]✓[/green] Removed {dep_type}/{dep_name}")
                else:
                    console.print(f"  [yellow]![/yellow] Failed to remove {dep_type}/{dep_name}")
