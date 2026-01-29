"""Core functionality for CPM."""

from .config import load_cpm_config, save_cpm_config, load_project_config, save_project_config
from .linker import (
    create_symlink,
    sync_project_links,
    remove_project_links,
    get_local_components,
    get_shared_components,
    update_component_gitignore,
)
from .resolver import resolve_project

__all__ = [
    "load_cpm_config",
    "save_cpm_config",
    "load_project_config",
    "save_project_config",
    "create_symlink",
    "sync_project_links",
    "remove_project_links",
    "get_local_components",
    "get_shared_components",
    "update_component_gitignore",
    "resolve_project",
]
