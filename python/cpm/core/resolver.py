"""Project resolution for CPM."""

from pathlib import Path
from typing import Any, Optional

from ..utils.fs import find_repo_root
from .config import (
    get_project_path,
    load_cpm_config,
    load_component_metadata,
    load_project_config,
)


def resolve_component(
    component_type: str, component_name: str, shared_dir: Path
) -> Optional[dict[str, Any]]:
    """Resolve a single component from the shared directory.

    Args:
        component_type: Type of component (skills, agents, hooks, rules).
        component_name: Name of the component.
        shared_dir: Path to the shared directory.

    Returns:
        Dictionary with component info, or None if not found.
    """
    component_path = shared_dir / component_type / component_name

    if not component_path.exists():
        return None

    # Get list of files in the component
    if component_path.is_dir():
        files = [f.name for f in component_path.iterdir() if f.is_file()]
    else:
        files = [component_path.name]
        component_path = component_path.parent

    return {
        "name": component_name,
        "type": "shared",
        "sourcePath": str(component_path.relative_to(shared_dir.parent)),
        "files": sorted(files),
    }


def resolve_local_component(
    component_type: str, component_name: str, project_path: Path
) -> Optional[dict[str, Any]]:
    """Resolve a single local component from the project directory.

    Args:
        component_type: Type of component (skills, agents, hooks, rules).
        component_name: Name of the component.
        project_path: Path to the project directory.

    Returns:
        Dictionary with component info, or None if not found.
    """
    component_path = project_path / ".claude" / component_type / component_name

    if not component_path.exists() or component_path.is_symlink():
        return None

    # Get list of files in the component
    if component_path.is_dir():
        files = [f.name for f in component_path.iterdir() if f.is_file()]
    else:
        files = [component_path.name]

    return {
        "name": component_name,
        "type": "local",
        "sourcePath": f".claude/{component_type}/{component_name}",
        "files": sorted(files),
    }


def get_local_components_in_project(project_path: Path) -> dict[str, list[dict[str, Any]]]:
    """Get all local (non-symlinked) components in a project.

    Args:
        project_path: Path to the project directory.

    Returns:
        Dictionary mapping component types to lists of component info.
    """
    claude_dir = project_path / ".claude"
    result = {"skills": [], "agents": [], "hooks": [], "rules": []}

    for component_type in result.keys():
        type_dir = claude_dir / component_type
        if not type_dir.exists():
            continue

        for item in type_dir.iterdir():
            # Skip .gitignore and symlinks
            if item.name == ".gitignore" or item.is_symlink():
                continue

            component = resolve_local_component(component_type, item.name, project_path)
            if component:
                result[component_type].append(component)

    return result


def resolve_project(
    project_path_or_name: str, repo_root: Optional[Path] = None
) -> dict[str, Any]:
    """Resolve a project and all its dependencies.

    Args:
        project_path_or_name: Path to the project directory or project name.
        repo_root: Path to the repo root. If None, will search for it.

    Returns:
        Dictionary with resolved project info.

    Raises:
        FileNotFoundError: If the project is not found.
    """
    if repo_root is None:
        repo_root = find_repo_root()
        if repo_root is None:
            raise FileNotFoundError("Not in a CPM mono repo")

    # Try to resolve as path first
    project_path = Path(project_path_or_name)
    if not project_path.is_absolute():
        # Check if it's a relative path
        full_path = repo_root / project_path_or_name
        if full_path.exists() and (full_path / "project.json").exists():
            project_path = full_path
        else:
            # Try as project name
            project_path = get_project_path(project_path_or_name, repo_root)

    if project_path is None or not project_path.exists():
        raise FileNotFoundError(f"Project not found: {project_path_or_name}")

    cpm_config = load_cpm_config(repo_root)
    project_config = load_project_config(project_path)

    shared_dir = repo_root / cpm_config.shared_dir

    # Resolve shared dependencies
    shared = {"skills": [], "agents": [], "hooks": [], "rules": []}

    dep_types = [
        ("skills", project_config.dependencies.skills),
        ("agents", project_config.dependencies.agents),
        ("hooks", project_config.dependencies.hooks),
        ("rules", project_config.dependencies.rules),
    ]

    for dep_type, deps in dep_types:
        for dep_name in deps:
            component = resolve_component(dep_type, dep_name, shared_dir)
            if component:
                shared[dep_type].append(component)

    # Get local components
    local = get_local_components_in_project(project_path)

    return {
        "name": project_config.name,
        "path": str(project_path.resolve()),
        "config": project_config.model_dump(exclude_none=True),
        "shared": shared,
        "local": local,
    }


def list_shared_components(
    repo_root: Optional[Path] = None,
) -> dict[str, list[str]]:
    """List all shared components in the mono repo.

    Args:
        repo_root: Path to the repo root. If None, will search for it.

    Returns:
        Dictionary mapping component types to lists of component names.
    """
    if repo_root is None:
        repo_root = find_repo_root()
        if repo_root is None:
            return {"skills": [], "agents": [], "hooks": [], "rules": []}

    cpm_config = load_cpm_config(repo_root)
    shared_dir = repo_root / cpm_config.shared_dir

    result = {}
    for component_type in ["skills", "agents", "hooks", "rules"]:
        type_dir = shared_dir / component_type
        if type_dir.exists():
            result[component_type] = sorted(
                [d.name for d in type_dir.iterdir() if d.is_dir()]
            )
        else:
            result[component_type] = []

    return result


def resolve_component_dependencies(
    comp_type: str,
    comp_name: str,
    repo_root: Path,
    resolved: Optional[set[str]] = None,
) -> list[tuple[str, str]]:
    """Recursively resolve all dependencies of a component.

    Args:
        comp_type: Component type (skills, agents, hooks, rules).
        comp_name: Component name.
        repo_root: Path to the repo root.
        resolved: Set of already resolved components (for circular detection).

    Returns:
        List of (comp_type, comp_name) tuples for all dependencies.

    Raises:
        ValueError: If circular dependency detected.
    """
    if resolved is None:
        resolved = set()

    component_key = f"{comp_type}:{comp_name}"

    if component_key in resolved:
        return []  # Already resolved

    resolved.add(component_key)

    metadata = load_component_metadata(comp_type, comp_name, repo_root)
    if metadata is None:
        return []

    dependencies = []

    # Process each dependency type
    for dep_type in ["skills", "agents", "hooks", "rules"]:
        dep_list = getattr(metadata.dependencies, dep_type, [])
        for dep_name in dep_list:
            dep_key = f"{dep_type}:{dep_name}"

            # Check for circular dependency in current resolution path
            if dep_key in resolved:
                # It's only circular if we're currently resolving it
                # (not if it was resolved in a different branch)
                continue

            dependencies.append((dep_type, dep_name))

            # Recursively resolve sub-dependencies
            sub_deps = resolve_component_dependencies(
                dep_type, dep_name, repo_root, resolved.copy()
            )
            dependencies.extend(sub_deps)

    return dependencies


def get_all_dependencies_for_component(
    comp_type: str, comp_name: str, repo_root: Path
) -> dict[str, list[str]]:
    """Get all dependencies for a component, organized by type.

    Args:
        comp_type: Component type (skills, agents, hooks, rules).
        comp_name: Component name.
        repo_root: Path to the repo root.

    Returns:
        Dictionary mapping component types to lists of component names.
    """
    deps = resolve_component_dependencies(comp_type, comp_name, repo_root)

    result: dict[str, list[str]] = {"skills": [], "agents": [], "hooks": [], "rules": []}

    seen = set()
    for dep_type, dep_name in deps:
        key = f"{dep_type}:{dep_name}"
        if key not in seen:
            seen.add(key)
            result[dep_type].append(dep_name)

    return result
