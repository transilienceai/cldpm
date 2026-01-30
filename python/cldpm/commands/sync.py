"""Implementation of cldpm sync command."""

from typing import Optional

import click

from ..core.config import get_project_path, list_projects
from ..core.linker import remove_project_links, sync_project_links
from ..utils.fs import find_repo_root
from ..utils.output import console, print_error, print_success, print_warning


@click.command()
@click.argument("project_name", required=False)
@click.option("--all", "-a", "sync_all", is_flag=True, help="Sync all projects")
def sync(project_name: Optional[str], sync_all: bool) -> None:
    """Regenerate symlinks for shared components.

    Recreates symlinks from project's .claude/ directories to shared/
    based on dependencies in project.json. Also updates per-directory
    .gitignore files to ignore only the symlinked components.

    \b
    When to use:
      - After 'git clone' (symlinks aren't committed)
      - After adding dependencies to project.json manually
      - When symlinks are broken or missing

    \b
    Note: Local (project-specific) components are not affected.

    \b
    Examples:
      cldpm sync my-project     # Single project
      cldpm sync --all          # All projects
      cldpm sync -a             # All projects (short)
    """
    # Find repo root
    repo_root = find_repo_root()
    if repo_root is None:
        print_error("Not in a CLDPM mono repo. Run 'cldpm init' first.")
        raise SystemExit(1)

    # Determine which projects to sync
    if sync_all:
        projects = list_projects(repo_root)
        if not projects:
            print_warning("No projects found in mono repo")
            return
    elif project_name:
        project_path = get_project_path(project_name, repo_root)
        if project_path is None:
            print_error(f"Project not found: {project_name}")
            raise SystemExit(1)
        projects = [project_path]
    else:
        print_error("Specify a project name or use --all to sync all projects")
        raise SystemExit(1)

    # Sync each project
    for project_path in projects:
        project_name = project_path.name

        # Remove existing symlinks
        remove_project_links(project_path)

        # Create fresh symlinks
        result = sync_project_links(project_path, repo_root)

        # Report results
        if result["created"]:
            print_success(f"{project_name}: synced {len(result['created'])} links")
            for link in result["created"]:
                console.print(f"  [green]✓[/green] {link}")
        elif not result["missing"] and not result["failed"]:
            console.print(f"[dim]{project_name}: no dependencies to sync[/dim]")

        if result["missing"]:
            print_warning(f"{project_name}: {len(result['missing'])} missing components")
            for link in result["missing"]:
                console.print(f"  [yellow]![/yellow] {link}")

        if result["failed"]:
            print_error(f"{project_name}: {len(result['failed'])} failed links")
            for link in result["failed"]:
                console.print(f"  [red]✗[/red] {link}")

        if result["skipped"]:
            console.print(
                f"  [dim]Skipped {len(result['skipped'])} existing files[/dim]"
            )
