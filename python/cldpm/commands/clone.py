"""Implementation of cldpm clone command."""

import json
import shutil
from pathlib import Path

import click

from ..core.config import load_cldpm_config, load_project_config
from ..core.resolver import resolve_project
from ..utils.fs import ensure_dir, find_repo_root
from ..utils.output import console, print_error, print_success, print_dir_tree


@click.command()
@click.argument("project_name")
@click.argument("directory")
@click.option(
    "--include-shared",
    is_flag=True,
    help="Also copy the full shared/ directory structure",
)
@click.option(
    "--preserve-links",
    is_flag=True,
    help="Keep symlinks instead of copying (requires shared/ to exist)",
)
def clone(
    project_name: str,
    directory: str,
    include_shared: bool,
    preserve_links: bool,
) -> None:
    """Clone a project to a standalone directory with all dependencies.

    Creates a complete, standalone copy of the project:
      - Shared components: Resolved from symlinks, copied as actual files
      - Local components: Copied directly

    \b
    Use cases:
      - Export project to work outside the mono repo
      - Share project with someone without the mono repo
      - Create a snapshot with all dependencies

    \b
    Examples:
      cldpm clone my-project ./standalone
      cldpm clone my-project /path/to/output
      cldpm clone my-project ./export --include-shared
      cldpm clone my-project ./linked --preserve-links
    """
    # Find repo root
    repo_root = find_repo_root()
    if repo_root is None:
        print_error("Not in a CLDPM mono repo. Run 'cldpm init' first.")
        raise SystemExit(1)

    # Resolve project
    try:
        resolved = resolve_project(project_name, repo_root)
    except FileNotFoundError as e:
        print_error(str(e))
        raise SystemExit(1)

    # Get source project path
    source_path = Path(resolved["path"])
    target_path = Path(directory).resolve()

    # Check if target exists
    if target_path.exists():
        print_error(f"Target directory already exists: {target_path}")
        raise SystemExit(1)

    # Create target directory
    ensure_dir(target_path)

    # Copy project files (excluding .claude subdirectories that are symlinks)
    for item in source_path.iterdir():
        dest = target_path / item.name

        if item.name == ".claude":
            # Handle .claude directory specially
            ensure_dir(dest)
            for claude_item in item.iterdir():
                claude_dest = dest / claude_item.name

                if claude_item.name in ["skills", "agents", "hooks", "rules"]:
                    # Create directory, will be populated below
                    ensure_dir(claude_dest)

                    # Copy local (non-symlink) components directly
                    for comp_item in claude_item.iterdir():
                        if comp_item.name == ".gitignore":
                            continue  # Skip .gitignore, will regenerate if needed
                        if not comp_item.is_symlink():
                            comp_dest = claude_dest / comp_item.name
                            if comp_item.is_dir():
                                shutil.copytree(comp_item, comp_dest)
                            else:
                                shutil.copy2(comp_item, comp_dest)
                elif claude_item.is_file():
                    shutil.copy2(claude_item, claude_dest)
                elif claude_item.is_dir():
                    shutil.copytree(claude_item, claude_dest)
        elif item.is_dir():
            shutil.copytree(item, dest, symlinks=preserve_links)
        else:
            shutil.copy2(item, dest)

    # Copy shared dependencies
    cldpm_config = load_cldpm_config(repo_root)
    shared_dir = repo_root / cldpm_config.shared_dir

    shared_counts = {}
    for dep_type in ["skills", "agents", "hooks", "rules"]:
        count = 0
        for component in resolved["shared"].get(dep_type, []):
            comp_name = component["name"]
            source_comp = shared_dir / dep_type / comp_name
            target_comp = target_path / ".claude" / dep_type / comp_name

            if source_comp.exists() and not target_comp.exists():
                if preserve_links:
                    # Create symlink (will only work if shared/ is accessible)
                    target_comp.symlink_to(source_comp)
                else:
                    # Copy actual files
                    if source_comp.is_dir():
                        shutil.copytree(source_comp, target_comp)
                    else:
                        shutil.copy2(source_comp, target_comp)
                count += 1
        shared_counts[dep_type] = count

    # Count local components
    local_counts = {
        dep_type: len(resolved["local"].get(dep_type, []))
        for dep_type in ["skills", "agents", "hooks", "rules"]
    }

    # Optionally copy full shared directory
    if include_shared:
        target_shared = target_path / "shared"
        shutil.copytree(shared_dir, target_shared)

        # Also copy cldpm.json for reference
        shutil.copy2(repo_root / "cldpm.json", target_path / "cldpm.json")

    # Update settings.json if it references hooks
    settings_path = target_path / ".claude" / "settings.json"
    if settings_path.exists():
        try:
            with open(settings_path) as f:
                settings = json.load(f)

            # Update any hook paths to be relative to the cloned project
            # (This is a placeholder - actual hook path updates would depend on the hook format)

            with open(settings_path, "w") as f:
                json.dump(settings, f, indent=2)
                f.write("\n")
        except (json.JSONDecodeError, IOError):
            pass  # Ignore settings.json issues

    print_success(f"Cloned {project_name} to {target_path}")

    # Show what was copied
    non_zero_shared = {k: v for k, v in shared_counts.items() if v > 0}
    non_zero_local = {k: v for k, v in local_counts.items() if v > 0}

    if non_zero_shared:
        deps_str = ", ".join(f"{v} {k}" for k, v in non_zero_shared.items())
        console.print(f"  Shared: {deps_str}")

    if non_zero_local:
        deps_str = ", ".join(f"{v} {k}" for k, v in non_zero_local.items())
        console.print(f"  Local: {deps_str}")

    if include_shared:
        console.print("  Included: full shared/ directory")

    console.print()
    print_dir_tree(target_path, max_depth=3)
