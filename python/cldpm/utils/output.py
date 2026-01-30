"""CLI output formatting utilities using rich."""

from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree

console = Console()


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[red]Error:[/red] {message}")


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[green]✓[/green] {message}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[yellow]Warning:[/yellow] {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"[blue]Info:[/blue] {message}")


def print_tree(data: dict[str, Any], title: str = "Project") -> None:
    """Print a tree representation of project data.

    Args:
        data: Project data dictionary.
        title: Title for the tree.
    """
    tree = Tree(f"[bold]{title}[/bold]: {data.get('name', 'Unknown')}")

    # Add path
    if "path" in data:
        tree.add(f"[dim]Path:[/dim] {data['path']}")

    # Add config info
    if "config" in data:
        config = data["config"]
        config_branch = tree.add("[bold]Config[/bold]")
        if config.get("description"):
            config_branch.add(f"Description: {config['description']}")

    # Add shared components
    if "shared" in data:
        shared = data["shared"]
        has_shared = any(shared.get(t) for t in ["skills", "agents", "hooks", "rules"])
        if has_shared:
            shared_branch = tree.add("[bold]Shared Components[/bold] [dim](from shared/)[/dim]")
            _add_component_items(shared_branch, shared)

    # Add local components
    if "local" in data:
        local = data["local"]
        has_local = any(local.get(t) for t in ["skills", "agents", "hooks", "rules"])
        if has_local:
            local_branch = tree.add("[bold]Local Components[/bold] [dim](project-specific)[/dim]")
            _add_component_items(local_branch, local)

    # Backward compatibility: handle old "resolved" format
    if "resolved" in data and "shared" not in data:
        resolved = data["resolved"]
        deps_branch = tree.add("[bold]Dependencies[/bold]")
        _add_component_items(deps_branch, resolved)

    console.print(tree)


def _add_component_items(parent_branch: Tree, components: dict[str, list]) -> None:
    """Add component items to a tree branch.

    Args:
        parent_branch: The parent tree branch to add items to.
        components: Dictionary mapping component types to lists of component info.
    """
    for dep_type in ["skills", "agents", "hooks", "rules"]:
        items = components.get(dep_type, [])
        if items:
            type_branch = parent_branch.add(f"[cyan]{dep_type}[/cyan]")
            for item in items:
                name = item['name']
                comp_type = item.get('type', 'shared')
                color = "green" if comp_type == "shared" else "yellow"
                item_branch = type_branch.add(f"[{color}]{name}[/{color}]")
                item_branch.add(f"[dim]Source:[/dim] {item['sourcePath']}")
                if item.get("files"):
                    files_str = ", ".join(item["files"])
                    item_branch.add(f"[dim]Files:[/dim] {files_str}")


def print_dir_tree(path: Path, prefix: str = "", max_depth: int = 3, current_depth: int = 0) -> None:
    """Print a directory tree.

    Args:
        path: Root path to display.
        prefix: Prefix for indentation.
        max_depth: Maximum depth to traverse.
        current_depth: Current depth level.
    """
    if current_depth >= max_depth:
        return

    if not path.exists():
        return

    items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))

    for i, item in enumerate(items):
        is_last = i == len(items) - 1
        connector = "└── " if is_last else "├── "

        # Format name with symlink indicator
        name = item.name
        if item.is_symlink():
            target = item.resolve()
            name = f"{name} -> {target}"
            console.print(f"{prefix}{connector}[cyan]{name}[/cyan]")
        elif item.is_dir():
            console.print(f"{prefix}{connector}[bold blue]{name}/[/bold blue]")
            # Recurse into directory
            extension = "    " if is_last else "│   "
            print_dir_tree(item, prefix + extension, max_depth, current_depth + 1)
        else:
            console.print(f"{prefix}{connector}{name}")
