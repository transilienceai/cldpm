"""Implementation of cldpm get command."""

import json
import shutil
import subprocess
from pathlib import Path
from typing import Optional

import click

from ..core.config import load_cldpm_config
from ..core.resolver import resolve_project
from ..utils.fs import ensure_dir, find_repo_root
from ..utils.git import (
    cleanup_temp_dir,
    clone_to_temp,
    get_github_token,
    has_sparse_clone_support,
    parse_repo_url,
    sparse_clone_to_temp,
)
from ..utils.output import console, print_error, print_success, print_tree, print_warning


@click.command()
@click.argument("path_or_name")
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["json", "tree"]),
    default="tree",
    help="Output format",
)
@click.option(
    "--remote",
    "-r",
    "remote_url",
    help="Git repository URL (uses GITHUB_TOKEN or GH_TOKEN env var for auth)",
)
@click.option(
    "--download",
    "-d",
    is_flag=True,
    help="Download/copy project with all dependencies to output directory",
)
@click.option(
    "--output",
    "-o",
    "output_dir",
    help="Output directory for download (default: project name)",
)
@click.option(
    "--branch",
    "-b",
    "branch_name",
    help="Git branch name (use when branch contains slashes)",
)
def get(
    path_or_name: str,
    output_format: str,
    remote_url: Optional[str],
    download: bool,
    output_dir: Optional[str],
    branch_name: Optional[str],
) -> None:
    """Get project info with all components (shared and local).

    Shows both shared components (from shared/, symlinked) and local
    components (project-specific, in .claude/).

    \b
    Output includes:
      - Project config from project.json
      - Shared components (symlinked from shared/)
      - Local components (project-specific in .claude/)

    \b
    Download option (-d):
      Works for both local and remote repos. Copies the project with
      all dependencies resolved (shared components copied as files).

    \b
    Remote URL formats:
      owner/repo                    - GitHub shorthand
      github.com/owner/repo         - Without https://
      https://github.com/owner/repo - Full URL

    \b
    Branch option (-b):
      Use when branch name contains slashes (e.g., feature/my-feature).
      This overrides any branch detected from the URL.

    \b
    Environment variables for private repos:
      GITHUB_TOKEN or GH_TOKEN

    \b
    Examples:
      cldpm get my-project                      # Show project info
      cldpm get my-project -f json              # JSON output
      cldpm get my-project -d                   # Download to ./my-project
      cldpm get my-project -d -o ./copy         # Download to ./copy
      cldpm get my-project -r owner/repo        # From remote
      cldpm get my-project -r owner/repo -d     # Download remote
      cldpm get my-project -r owner/repo -b feature/auth  # With branch
    """
    if remote_url:
        _handle_remote_get(
            path_or_name, output_format, remote_url, download, output_dir, branch_name
        )
    else:
        _handle_local_get(path_or_name, output_format, download, output_dir)


def _handle_local_get(
    path_or_name: str,
    output_format: str,
    download: bool,
    output_dir: Optional[str],
) -> None:
    """Handle get command for local repositories."""
    # Find repo root
    repo_root = find_repo_root()
    if repo_root is None:
        print_error("Not in a CLDPM mono repo. Run 'cldpm init' first.")
        raise SystemExit(1)

    # Resolve project
    try:
        result = resolve_project(path_or_name, repo_root)
    except FileNotFoundError as e:
        print_error(str(e))
        raise SystemExit(1)

    # Output in requested format
    if output_format == "json":
        click.echo(json.dumps(result, indent=2))
    else:
        print_tree(result)

    # Download if requested
    if download:
        _download_local_project(result, repo_root, output_dir)


def _download_local_project(
    resolved: dict,
    repo_root: Path,
    output_dir: Optional[str],
) -> None:
    """Download/copy a local project with all dependencies resolved."""
    source_path = Path(resolved["path"])
    project_name = resolved["name"]

    # Determine target directory
    if output_dir:
        target_path = Path(output_dir).resolve()
    else:
        target_path = Path.cwd() / project_name

    if target_path.exists():
        print_error(f"Target directory already exists: {target_path}")
        raise SystemExit(1)

    # Create target directory
    ensure_dir(target_path)

    # Load CLDPM config for shared directory path
    cldpm_config = load_cldpm_config(repo_root)
    shared_dir = repo_root / cldpm_config.shared_dir

    # Copy project files
    for item in source_path.iterdir():
        dest = target_path / item.name

        if item.name == ".claude":
            # Handle .claude directory specially
            ensure_dir(dest)
            for claude_item in item.iterdir():
                claude_dest = dest / claude_item.name

                if claude_item.name in ["skills", "agents", "hooks", "rules"]:
                    # Create directory
                    ensure_dir(claude_dest)

                    # Copy local (non-symlink) components directly
                    for comp_item in claude_item.iterdir():
                        if comp_item.name == ".gitignore":
                            continue  # Skip .gitignore
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
            shutil.copytree(item, dest, symlinks=False)
        else:
            shutil.copy2(item, dest)

    # Copy shared dependencies (resolve symlinks to actual files)
    for dep_type in ["skills", "agents", "hooks", "rules"]:
        for component in resolved["shared"].get(dep_type, []):
            comp_name = component["name"]
            source_comp = shared_dir / dep_type / comp_name
            target_comp = target_path / ".claude" / dep_type / comp_name

            if source_comp.exists() and not target_comp.exists():
                if source_comp.is_dir():
                    shutil.copytree(source_comp, target_comp)
                else:
                    shutil.copy2(source_comp, target_comp)

    # Count what was copied
    shared_counts = {
        dep_type: len(resolved["shared"].get(dep_type, []))
        for dep_type in ["skills", "agents", "hooks", "rules"]
    }
    local_counts = {
        dep_type: len(resolved["local"].get(dep_type, []))
        for dep_type in ["skills", "agents", "hooks", "rules"]
    }

    print_success(f"Downloaded to {target_path}")

    non_zero_shared = {k: v for k, v in shared_counts.items() if v > 0}
    non_zero_local = {k: v for k, v in local_counts.items() if v > 0}

    if non_zero_shared:
        deps_str = ", ".join(f"{v} {k}" for k, v in non_zero_shared.items())
        console.print(f"  Shared: {deps_str}")

    if non_zero_local:
        deps_str = ", ".join(f"{v} {k}" for k, v in non_zero_local.items())
        console.print(f"  Local: {deps_str}")


def _handle_remote_get(
    path_or_name: str,
    output_format: str,
    remote_url: str,
    download: bool,
    output_dir: Optional[str],
    branch_name: Optional[str] = None,
) -> None:
    """Handle get command for remote repositories."""
    # Get GitHub token
    token = get_github_token()
    if not token:
        print_warning(
            "No GITHUB_TOKEN or GH_TOKEN found. Private repos may not be accessible."
        )

    # Parse the remote URL
    try:
        repo_url, _subpath, url_branch = parse_repo_url(remote_url)
    except ValueError as e:
        print_error(str(e))
        raise SystemExit(1)

    # Use explicit branch if provided, otherwise use branch from URL
    branch = branch_name if branch_name else url_branch

    # Check if sparse clone is supported
    use_sparse = has_sparse_clone_support()

    if use_sparse:
        _handle_remote_get_sparse(
            path_or_name, output_format, remote_url, download, output_dir,
            repo_url, branch, token
        )
    else:
        _handle_remote_get_full(
            path_or_name, output_format, remote_url, download, output_dir,
            repo_url, branch, token
        )


def _handle_remote_get_sparse(
    path_or_name: str,
    output_format: str,
    remote_url: str,
    download: bool,
    output_dir: Optional[str],
    repo_url: str,
    branch: Optional[str],
    token: Optional[str],
) -> None:
    """Handle remote get using sparse checkout (optimized)."""
    temp_config = None
    temp_dir = None

    try:
        # Phase 1: Get config files only (tiny download)
        console.print(f"[dim]Fetching project config from {repo_url}...[/dim]")
        config_paths = ["cldpm.json"]
        temp_config = sparse_clone_to_temp(repo_url, config_paths, branch, token)

        # Parse cldpm.json to get directories
        cldpm_json_path = temp_config / "cldpm.json"
        if not cldpm_json_path.exists():
            print_error("Remote repository is not a CLDPM mono repo (no cldpm.json found)")
            raise SystemExit(1)

        with open(cldpm_json_path) as f:
            cldpm_config = json.load(f)

        projects_dir = cldpm_config.get("projectsDir", "projects")
        shared_dir = cldpm_config.get("sharedDir", "shared")
        project_path = f"{projects_dir}/{path_or_name}"

        cleanup_temp_dir(temp_config)
        temp_config = None

        # Phase 2: Get project.json to find dependencies
        console.print(f"[dim]Fetching project metadata...[/dim]")
        project_config_paths = [f"{project_path}/project.json"]
        temp_project = sparse_clone_to_temp(repo_url, project_config_paths, branch, token)

        project_json_path = temp_project / project_path / "project.json"
        if not project_json_path.exists():
            cleanup_temp_dir(temp_project)
            print_error(f"Project not found: {path_or_name}")
            raise SystemExit(1)

        with open(project_json_path) as f:
            project_config = json.load(f)

        cleanup_temp_dir(temp_project)

        # Build path list for final sparse clone
        all_paths = [project_path]
        dependencies = project_config.get("dependencies", {})
        for dep_type in ["skills", "agents", "hooks", "rules"]:
            for dep_name in dependencies.get(dep_type, []):
                all_paths.append(f"{shared_dir}/{dep_type}/{dep_name}")

        # Phase 3: Download everything needed
        console.print(f"[dim]Downloading project and dependencies...[/dim]")
        temp_dir = sparse_clone_to_temp(repo_url, all_paths, branch, token)

        # Build result for display
        result = _build_sparse_result(
            temp_dir, path_or_name, project_path, shared_dir,
            project_config, dependencies, remote_url, repo_url, branch
        )

        # Output the result
        if output_format == "json":
            click.echo(json.dumps(result, indent=2))
        else:
            print_tree(result)
            console.print(f"\n[dim]Source: {remote_url}[/dim]")

        # Download if requested
        if download:
            _download_sparse_project(
                temp_dir, output_dir, path_or_name, project_path,
                shared_dir, dependencies, repo_url
            )
            cleanup_temp_dir(temp_dir)
            temp_dir = None

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        if "Authentication failed" in error_msg or "could not read" in error_msg:
            print_error(
                "Authentication failed. Set GITHUB_TOKEN or GH_TOKEN environment variable."
            )
        else:
            print_error(f"Git error: {error_msg}")
        raise SystemExit(1)
    finally:
        if temp_config:
            cleanup_temp_dir(temp_config)
        if temp_dir and not download:
            cleanup_temp_dir(temp_dir)


def _handle_remote_get_full(
    path_or_name: str,
    output_format: str,
    remote_url: str,
    download: bool,
    output_dir: Optional[str],
    repo_url: str,
    branch: Optional[str],
    token: Optional[str],
) -> None:
    """Handle remote get using full clone (fallback for old Git versions)."""
    temp_dir = None
    try:
        # Clone to temporary directory
        console.print(f"[dim]Cloning {repo_url}...[/dim]")
        temp_dir = clone_to_temp(repo_url, branch, token)

        # Check if it's a valid CLDPM repo
        if not (temp_dir / "cldpm.json").exists():
            print_error("Remote repository is not a CLDPM mono repo (no cldpm.json found)")
            raise SystemExit(1)

        # Resolve the project
        try:
            result = resolve_project(path_or_name, temp_dir)
        except FileNotFoundError as e:
            print_error(str(e))
            raise SystemExit(1)

        # Add remote info to result
        result["remote"] = {
            "url": remote_url,
            "repo_url": repo_url,
            "branch": branch,
        }

        # Output the result
        if output_format == "json":
            click.echo(json.dumps(result, indent=2))
        else:
            print_tree(result)
            console.print(f"\n[dim]Source: {remote_url}[/dim]")

        # Download if requested
        if download:
            _download_remote_project(result, temp_dir, output_dir, repo_url)

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        if "Authentication failed" in error_msg or "could not read" in error_msg:
            print_error(
                "Authentication failed. Set GITHUB_TOKEN or GH_TOKEN environment variable."
            )
        else:
            print_error(f"Git error: {error_msg}")
        raise SystemExit(1)
    finally:
        # Clean up temp directory if not downloading
        if temp_dir and not download:
            cleanup_temp_dir(temp_dir)


def _build_sparse_result(
    temp_dir: Path,
    project_name: str,
    project_path: str,
    shared_dir: str,
    project_config: dict,
    dependencies: dict,
    remote_url: str,
    repo_url: str,
    branch: Optional[str],
) -> dict:
    """Build the result dictionary for sparse clone output."""
    source_project = temp_dir / project_path

    result = {
        "name": project_name,
        "path": str(source_project),
        "config": project_config,
        "shared": {},
        "local": {},
        "remote": {
            "url": remote_url,
            "repo_url": repo_url,
            "branch": branch,
        },
    }

    # Build shared components info
    for dep_type in ["skills", "agents", "hooks", "rules"]:
        result["shared"][dep_type] = []
        for dep_name in dependencies.get(dep_type, []):
            source_comp = temp_dir / shared_dir / dep_type / dep_name
            if source_comp.exists():
                # Get list of files in the component
                files = []
                if source_comp.is_dir():
                    files = [f.name for f in source_comp.iterdir() if f.is_file()]
                result["shared"][dep_type].append({
                    "name": dep_name,
                    "type": "shared",
                    "sourcePath": f"{shared_dir}/{dep_type}/{dep_name}",
                    "files": files,
                })

    # Build local components info
    claude_dir = source_project / ".claude"
    for dep_type in ["skills", "agents", "hooks", "rules"]:
        result["local"][dep_type] = []
        type_dir = claude_dir / dep_type
        if type_dir.exists():
            for item in type_dir.iterdir():
                if item.name != ".gitignore" and not item.is_symlink():
                    # Get list of files in the component
                    files = []
                    if item.is_dir():
                        files = [f.name for f in item.iterdir() if f.is_file()]
                    result["local"][dep_type].append({
                        "name": item.name,
                        "type": "local",
                        "sourcePath": f".claude/{dep_type}/{item.name}",
                        "files": files,
                    })

    return result


def _download_sparse_project(
    temp_dir: Path,
    output_dir: Optional[str],
    project_name: str,
    project_path: str,
    shared_dir: str,
    dependencies: dict,
    repo_url: str,
) -> None:
    """Download a project from sparse clone with proper file placement."""
    # Determine target directory
    if output_dir:
        target = Path(output_dir).resolve()
    else:
        target = Path.cwd() / project_name

    if target.exists():
        print_error(f"Target directory already exists: {target}")
        raise SystemExit(1)

    source_project = temp_dir / project_path

    # Create target directory
    ensure_dir(target)

    # Copy project files
    for item in source_project.iterdir():
        dest = target / item.name

        if item.name == ".claude":
            # Handle .claude directory specially
            ensure_dir(dest)
            for claude_item in item.iterdir():
                claude_dest = dest / claude_item.name

                if claude_item.name in ["skills", "agents", "hooks", "rules"]:
                    # Create directory
                    ensure_dir(claude_dest)

                    # Copy local (non-symlink) components directly
                    for comp_item in claude_item.iterdir():
                        if comp_item.name == ".gitignore":
                            continue
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
            shutil.copytree(item, dest, symlinks=False)
        else:
            shutil.copy2(item, dest)

    # Place shared components directly in .claude/<type>/<name>/
    for dep_type in ["skills", "agents", "hooks", "rules"]:
        for dep_name in dependencies.get(dep_type, []):
            source_comp = temp_dir / shared_dir / dep_type / dep_name
            target_comp = target / ".claude" / dep_type / dep_name

            if source_comp.exists() and not target_comp.exists():
                ensure_dir(target_comp.parent)
                if source_comp.is_dir():
                    shutil.copytree(source_comp, target_comp)
                else:
                    shutil.copy2(source_comp, target_comp)

    # Count what was copied
    shared_counts = {
        dep_type: len(dependencies.get(dep_type, []))
        for dep_type in ["skills", "agents", "hooks", "rules"]
    }
    local_counts = {dep_type: 0 for dep_type in ["skills", "agents", "hooks", "rules"]}

    # Count local components
    claude_dir = source_project / ".claude"
    for dep_type in ["skills", "agents", "hooks", "rules"]:
        type_dir = claude_dir / dep_type
        if type_dir.exists():
            for item in type_dir.iterdir():
                if item.name != ".gitignore" and not item.is_symlink():
                    local_counts[dep_type] += 1

    print_success(f"Downloaded to {target}")
    console.print(f"  [dim]Source: {repo_url}[/dim]")

    non_zero_shared = {k: v for k, v in shared_counts.items() if v > 0}
    non_zero_local = {k: v for k, v in local_counts.items() if v > 0}

    if non_zero_shared:
        deps_str = ", ".join(f"{v} {k}" for k, v in non_zero_shared.items())
        console.print(f"  Shared: {deps_str}")

    if non_zero_local:
        deps_str = ", ".join(f"{v} {k}" for k, v in non_zero_local.items())
        console.print(f"  Local: {deps_str}")


def _download_remote_project(
    resolved: dict,
    temp_dir: Path,
    output_dir: Optional[str],
    repo_url: str,
) -> None:
    """Download a remote project with all dependencies resolved."""
    project_name = resolved["name"]

    # Determine target directory
    if output_dir:
        target = Path(output_dir).resolve()
    else:
        target = Path.cwd() / project_name

    if target.exists():
        print_error(f"Target directory already exists: {target}")
        raise SystemExit(1)

    # For remote, we copy the resolved project (similar to local download)
    # but from the temp directory
    cldpm_config = load_cldpm_config(temp_dir)
    shared_dir = temp_dir / cldpm_config.shared_dir
    source_path = Path(resolved["path"])

    # Create target directory
    ensure_dir(target)

    # Copy project files
    for item in source_path.iterdir():
        dest = target / item.name

        if item.name == ".claude":
            ensure_dir(dest)
            for claude_item in item.iterdir():
                claude_dest = dest / claude_item.name

                if claude_item.name in ["skills", "agents", "hooks", "rules"]:
                    ensure_dir(claude_dest)
                    for comp_item in claude_item.iterdir():
                        if comp_item.name == ".gitignore":
                            continue
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
            shutil.copytree(item, dest, symlinks=False)
        else:
            shutil.copy2(item, dest)

    # Copy shared dependencies
    for dep_type in ["skills", "agents", "hooks", "rules"]:
        for component in resolved["shared"].get(dep_type, []):
            comp_name = component["name"]
            source_comp = shared_dir / dep_type / comp_name
            target_comp = target / ".claude" / dep_type / comp_name

            if source_comp.exists() and not target_comp.exists():
                if source_comp.is_dir():
                    shutil.copytree(source_comp, target_comp)
                else:
                    shutil.copy2(source_comp, target_comp)

    # Clean up temp directory
    cleanup_temp_dir(temp_dir)

    print_success(f"Downloaded to {target}")
    console.print(f"  [dim]Source: {repo_url}[/dim]")
