"""CLI entry point for CPM."""

import click

from .commands import init, create, add, remove, link, unlink, get, clone, sync


@click.group()
@click.version_option(version="0.1.0", prog_name="cpm")
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


def main() -> None:
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
