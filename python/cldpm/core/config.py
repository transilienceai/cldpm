"""Configuration loading and saving for CLDPM."""

import json
from pathlib import Path
from typing import Optional

from ..schemas import CldpmConfig, ComponentMetadata, ProjectConfig
from ..utils.fs import find_repo_root


def load_cldpm_config(repo_root: Optional[Path] = None) -> CldpmConfig:
    """Load the cldpm.json configuration.

    Args:
        repo_root: Path to the repo root. If None, will search for it.

    Returns:
        The loaded CldpmConfig.

    Raises:
        FileNotFoundError: If cldpm.json is not found.
        ValueError: If cldpm.json is invalid.
    """
    if repo_root is None:
        repo_root = find_repo_root()
        if repo_root is None:
            raise FileNotFoundError(
                "Not in a CLDPM mono repo. Run 'cldpm init' to create one."
            )

    config_path = repo_root / "cldpm.json"
    if not config_path.exists():
        raise FileNotFoundError(f"cldpm.json not found at {config_path}")

    with open(config_path, "r") as f:
        data = json.load(f)

    return CldpmConfig.model_validate(data)


def save_cldpm_config(config: CldpmConfig, repo_root: Path) -> None:
    """Save the cldpm.json configuration.

    Args:
        config: The CldpmConfig to save.
        repo_root: Path to the repo root.
    """
    config_path = repo_root / "cldpm.json"
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

    config = load_cldpm_config(repo_root)
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

    config = load_cldpm_config(repo_root)
    projects_dir = repo_root / config.projects_dir

    if not projects_dir.exists():
        return []

    projects = []
    for item in projects_dir.iterdir():
        if item.is_dir() and (item / "project.json").exists():
            projects.append(item)

    return sorted(projects)


def load_component_metadata(
    comp_type: str, comp_name: str, repo_root: Path
) -> Optional[ComponentMetadata]:
    """Load metadata for a shared component.

    Looks for a metadata file (skill.json, agent.json, hook.json, rule.json)
    in the component directory.

    Args:
        comp_type: Component type (skills, agents, hooks, rules).
        comp_name: Component name.
        repo_root: Path to the repo root.

    Returns:
        ComponentMetadata if found, None otherwise.
    """
    config = load_cldpm_config(repo_root)
    shared_dir = repo_root / config.shared_dir

    component_path = shared_dir / comp_type / comp_name
    if not component_path.exists():
        return None

    # Try different metadata file names
    singular_type = comp_type.rstrip("s")  # skills -> skill
    metadata_files = [
        f"{singular_type}.json",  # skill.json, agent.json, etc.
        "metadata.json",  # Generic fallback
    ]

    for metadata_file in metadata_files:
        metadata_path = component_path / metadata_file
        if metadata_path.exists():
            with open(metadata_path, "r") as f:
                data = json.load(f)
            return ComponentMetadata.model_validate(data)

    # Return minimal metadata if no metadata file exists
    return ComponentMetadata(name=comp_name)
