"""Configuration loading and saving for CPM."""

import json
from pathlib import Path
from typing import Optional

from ..schemas import CpmConfig, ProjectConfig
from ..utils.fs import find_repo_root


def load_cpm_config(repo_root: Optional[Path] = None) -> CpmConfig:
    """Load the cpm.json configuration.

    Args:
        repo_root: Path to the repo root. If None, will search for it.

    Returns:
        The loaded CpmConfig.

    Raises:
        FileNotFoundError: If cpm.json is not found.
        ValueError: If cpm.json is invalid.
    """
    if repo_root is None:
        repo_root = find_repo_root()
        if repo_root is None:
            raise FileNotFoundError(
                "Not in a CPM mono repo. Run 'cpm init' to create one."
            )

    config_path = repo_root / "cpm.json"
    if not config_path.exists():
        raise FileNotFoundError(f"cpm.json not found at {config_path}")

    with open(config_path, "r") as f:
        data = json.load(f)

    return CpmConfig.model_validate(data)


def save_cpm_config(config: CpmConfig, repo_root: Path) -> None:
    """Save the cpm.json configuration.

    Args:
        config: The CpmConfig to save.
        repo_root: Path to the repo root.
    """
    config_path = repo_root / "cpm.json"
    with open(config_path, "w") as f:
        json.dump(config.model_dump(by_alias=True), f, indent=2)
        f.write("\n")


def load_project_config(project_path: Path) -> ProjectConfig:
    """Load a project.json configuration.

    Args:
        project_path: Path to the project directory.

    Returns:
        The loaded ProjectConfig.

    Raises:
        FileNotFoundError: If project.json is not found.
        ValueError: If project.json is invalid.
    """
    config_path = project_path / "project.json"
    if not config_path.exists():
        raise FileNotFoundError(f"project.json not found at {config_path}")

    with open(config_path, "r") as f:
        data = json.load(f)

    return ProjectConfig.model_validate(data)


def save_project_config(config: ProjectConfig, project_path: Path) -> None:
    """Save a project.json configuration.

    Args:
        config: The ProjectConfig to save.
        project_path: Path to the project directory.
    """
    config_path = project_path / "project.json"
    with open(config_path, "w") as f:
        json.dump(config.model_dump(exclude_none=True), f, indent=2)
        f.write("\n")


def get_project_path(
    project_name: str, repo_root: Optional[Path] = None
) -> Optional[Path]:
    """Get the path to a project by name.

    Args:
        project_name: Name of the project.
        repo_root: Path to the repo root. If None, will search for it.

    Returns:
        Path to the project directory, or None if not found.
    """
    if repo_root is None:
        repo_root = find_repo_root()
        if repo_root is None:
            return None

    config = load_cpm_config(repo_root)
    project_path = repo_root / config.projects_dir / project_name

    if project_path.exists() and (project_path / "project.json").exists():
        return project_path

    return None


def list_projects(repo_root: Optional[Path] = None) -> list[Path]:
    """List all projects in the mono repo.

    Args:
        repo_root: Path to the repo root. If None, will search for it.

    Returns:
        List of paths to project directories.
    """
    if repo_root is None:
        repo_root = find_repo_root()
        if repo_root is None:
            return []

    config = load_cpm_config(repo_root)
    projects_dir = repo_root / config.projects_dir

    if not projects_dir.exists():
        return []

    projects = []
    for item in projects_dir.iterdir():
        if item.is_dir() and (item / "project.json").exists():
            projects.append(item)

    return sorted(projects)
