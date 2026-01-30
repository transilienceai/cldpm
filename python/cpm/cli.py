"""CLI entry point for CPM."""

import click

from .commands import init, create, add, remove, link, unlink, get, clone, sync
from ._banner import print_banner


def show_version(ctx: click.Context, param: click.Parameter, value: bool) -> None:
    """Custom version callback that shows banner."""
    if not value or ctx.resilient_parsing:
        return
    print_banner()
    ctx.exit()


@click.group()
@click.option(
    "--version", "-v",
    is_flag=True,
    callback=show_version,
    expose_value=False,
    is_eager=True,
    help="Show version and info banner.",
)
def cli() -> None:
    """CPM - Claude Project Manager.

    An SDK and CLI for managing mono repos with multiple Claude Code projects.
    Supports both shared components (reusable across projects) and local
    components (project-specific).

    \b
    Component Types:
      - Shared: Stored in shared/, symlinked to projects, reusable
      - Local:  Stored in .claude/, project-specific, committed directly

    \b
    Quick Start:
      cpm init my-monorepo              # Create new mono repo
      cpm create project my-app         # Create new project
      cpm add skill:common --to my-app  # Add shared component
      cpm get my-app                    # View project info
      cpm clone my-app ./standalone     # Export with all deps
      cpm sync --all                    # Restore symlinks after git clone

    \b
    Crafted by Transilience.ai
    Authored by Aman Agarwal (https://github.com/amanagarwal041)
    """
    pass


# Register commands
cli.add_command(init)
cli.add_command(create)
cli.add_command(add)
cli.add_command(remove)
cli.add_command(link)
cli.add_command(unlink)
cli.add_command(get)
cli.add_command(clone)
cli.add_command(sync)


@cli.command()
def info() -> None:
    """Show CPM information banner.

    Displays version, quick start guide, and attribution.
    """
    print_banner()


def main() -> None:
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
