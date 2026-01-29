"""Symlink management for CPM projects."""

import os
from pathlib import Path
from typing import Optional

from ..schemas import ProjectConfig
from ..utils.fs import ensure_dir, find_repo_root
from .config import load_cpm_config, load_project_config


def create_symlink(source: Path, target: Path) -> bool:
    """Create a symlink from target to source.

    Args:
        source: The actual file/directory (symlink target).
        target: The symlink path to create.

    Returns:
        True if successful, False otherwise.
    """
    # Ensure parent directory exists
    ensure_dir(target.parent)

    # Remove existing symlink if present
    if target.is_symlink():
        target.unlink()
    elif target.exists():
        # Don't overwrite non-symlink files
        return False

    # Create relative symlink
    try:
        # Calculate relative path from target to source
        rel_path = os.path.relpath(source, target.parent)
        target.symlink_to(rel_path)
        return True
    except OSError:
        return False


def remove_project_links(project_path: Path) -> None:
    """Remove all symlinks in a project's .claude directory.

    Args:
        project_path: Path to the project directory.
    """
    claude_dir = project_path / ".claude"
    if not claude_dir.exists():
        return

    for subdir in ["skills", "agents", "hooks", "rules"]:
        subdir_path = claude_dir / subdir
        if not subdir_path.exists():
            continue

        for item in subdir_path.iterdir():
            if item.is_symlink():
                item.unlink()


def update_component_gitignore(component_dir: Path, symlinked_names: list[str]) -> None:
    """Update the .gitignore file in a component directory to ignore only symlinks.

    This allows project-specific components to be committed while shared
    symlinked components are ignored.

    Args:
        component_dir: Path to the component directory (e.g., .claude/skills/).
        symlinked_names: List of symlinked component names to ignore.
    """
    gitignore_path = component_dir / ".gitignore"

    if not symlinked_names:
        # No symlinks, remove .gitignore if it exists and only has our content
        if gitignore_path.exists():
            content = gitignore_path.read_text()
            if content.startswith("# CPM shared components"):
                gitignore_path.unlink()
        return

    # Generate .gitignore content
    lines = [
        "# CPM shared components (symlinks to shared/)",
        "# These are regenerated via 'cpm sync' - do not commit symlinks",
        "# Project-specific components in this directory WILL be committed",
        "",
    ]
    lines.extend(sorted(symlinked_names))
    lines.append("")  # Trailing newline

    gitignore_path.write_text("\n".join(lines))


def sync_project_links(
    project_path: Path, repo_root: Optional[Path] = None
) -> dict[str, list[str]]:
    """Synchronize symlinks for a project based on its dependencies.

    Args:
        project_path: Path to the project directory.
        repo_root: Path to the repo root. If None, will search for it.

    Returns:
        Dictionary with lists of created, failed, and skipped links.
    """
    if repo_root is None:
        repo_root = find_repo_root(project_path)
        if repo_root is None:
            raise ValueError("Not in a CPM mono repo")

    cpm_config = load_cpm_config(repo_root)
    project_config = load_project_config(project_path)

    shared_dir = repo_root / cpm_config.shared_dir
    claude_dir = project_path / ".claude"

    result = {"created": [], "failed": [], "skipped": [], "missing": []}

    # Process each dependency type
    dep_types = [
        ("skills", project_config.dependencies.skills),
        ("agents", project_config.dependencies.agents),
        ("hooks", project_config.dependencies.hooks),
        ("rules", project_config.dependencies.rules),
    ]

    for dep_type, deps in dep_types:
        target_dir = claude_dir / dep_type
        ensure_dir(target_dir)

        # Track successfully created symlinks for .gitignore
        symlinked_names = []

        for dep_name in deps:
            source = shared_dir / dep_type / dep_name
            target = target_dir / dep_name

            if not source.exists():
                result["missing"].append(f"{dep_type}/{dep_name}")
                continue

            if target.exists() and not target.is_symlink():
                # Local component exists with same name - skip but warn
                result["skipped"].append(f"{dep_type}/{dep_name}")
                continue

            if create_symlink(source, target):
                result["created"].append(f"{dep_type}/{dep_name}")
                symlinked_names.append(dep_name)
            else:
                result["failed"].append(f"{dep_type}/{dep_name}")

        # Also include existing symlinks that weren't just created
        for item in target_dir.iterdir():
            if item.is_symlink() and item.name not in symlinked_names:
                symlinked_names.append(item.name)

        # Update .gitignore in this component directory
        update_component_gitignore(target_dir, symlinked_names)

    return result


def add_component_link(
    project_path: Path,
    component_type: str,
    component_name: str,
    repo_root: Optional[Path] = None,
) -> bool:
    """Add a single component symlink to a project.

    Args:
        project_path: Path to the project directory.
        component_type: Type of component (skills, agents, hooks, rules).
        component_name: Name of the component.
        repo_root: Path to the repo root. If None, will search for it.

    Returns:
        True if successful, False otherwise.
    """
    if repo_root is None:
        repo_root = find_repo_root(project_path)
        if repo_root is None:
            raise ValueError("Not in a CPM mono repo")

    cpm_config = load_cpm_config(repo_root)
    shared_dir = repo_root / cpm_config.shared_dir

    source = shared_dir / component_type / component_name
    target = project_path / ".claude" / component_type / component_name

    if not source.exists():
        return False

    success = create_symlink(source, target)

    if success:
        # Update .gitignore in the component directory
        component_dir = project_path / ".claude" / component_type
        symlinked_names = [
            item.name for item in component_dir.iterdir() if item.is_symlink()
        ]
        update_component_gitignore(component_dir, symlinked_names)

    return success


def get_local_components(project_path: Path) -> dict[str, list[str]]:
    """Get list of local (non-symlinked) components in a project.

    Args:
        project_path: Path to the project directory.

    Returns:
        Dictionary mapping component types to lists of local component names.
    """
    claude_dir = project_path / ".claude"
    result = {}

    for component_type in ["skills", "agents", "hooks", "rules"]:
        type_dir = claude_dir / component_type
        if not type_dir.exists():
            result[component_type] = []
            continue

        local_components = []
        for item in type_dir.iterdir():
            # Skip .gitignore and symlinks
            if item.name == ".gitignore":
                continue
            if not item.is_symlink():
                local_components.append(item.name)

        result[component_type] = sorted(local_components)

    return result


def get_shared_components(project_path: Path) -> dict[str, list[str]]:
    """Get list of shared (symlinked) components in a project.

    Args:
        project_path: Path to the project directory.

    Returns:
        Dictionary mapping component types to lists of shared component names.
    """
    claude_dir = project_path / ".claude"
    result = {}

    for component_type in ["skills", "agents", "hooks", "rules"]:
        type_dir = claude_dir / component_type
        if not type_dir.exists():
            result[component_type] = []
            continue

        shared_components = []
        for item in type_dir.iterdir():
            if item.is_symlink():
                shared_components.append(item.name)

        result[component_type] = sorted(shared_components)

    return result
