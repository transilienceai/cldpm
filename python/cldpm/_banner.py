"""CLDPM Banner Display Module.

Displays decorative information about CLDPM, author, and Transilience.
"""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

BANNER_ASCII = r"""
    ██████╗██╗     ██████╗ ██████╗ ███╗   ███╗
   ██╔════╝██║     ██╔══██╗██╔══██╗████╗ ████║
   ██║     ██║     ██║  ██║██████╔╝██╔████╔██║
   ██║     ██║     ██║  ██║██╔═══╝ ██║╚██╔╝██║
   ╚██████╗███████╗██████╔╝██║     ██║ ╚═╝ ██║
    ╚═════╝╚══════╝╚═════╝ ╚═╝     ╚═╝     ╚═╝
"""


def print_banner(console: Console | None = None) -> None:
    """Print the CLDPM installation/info banner."""
    if console is None:
        console = Console()

    # ASCII art
    ascii_text = Text(BANNER_ASCII, style="bold magenta")
    console.print(ascii_text)

    # Title
    console.print("  [bold cyan]Claude Project Manager[/bold cyan]")
    console.print("  [dim]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/dim]")
    console.print()

    # Description
    console.print("  [white]Manage mono repos with multiple Claude Code[/white]")
    console.print("  [white]projects. Share skills, agents, hooks, and[/white]")
    console.print("  [white]rules across projects without duplication.[/white]")
    console.print()
    console.print("  [dim]─────────────────────────────────────────[/dim]")
    console.print()

    # Quick Start
    console.print("  [yellow]Quick Start:[/yellow]")
    console.print("  [dim]$[/dim] [white]cldpm init my-monorepo[/white]")
    console.print("  [dim]$[/dim] [white]cldpm create project web-app[/white]")
    console.print("  [dim]$[/dim] [white]cldpm create skill logging[/white]")
    console.print("  [dim]$[/dim] [white]cldpm add skill:logging --to web-app[/white]")
    console.print()
    console.print("  [dim]─────────────────────────────────────────[/dim]")
    console.print()

    # Attribution
    console.print("  [magenta]◆[/magenta] [dim]Crafted by[/dim] [cyan]Transilience.ai[/cyan]")
    console.print()
    console.print("  [dim]─────────────────────────────────────────[/dim]")
    console.print()

    # Links
    console.print("  [dim]Docs:[/dim]    [cyan]https://cldpm.transilience.ai[/cyan]")
    console.print("  [dim]GitHub:[/dim]  [cyan]https://github.com/transilienceai/cldpm[/cyan]")
    console.print()
    console.print("  [dim]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/dim]")
    console.print()


def get_banner_text() -> str:
    """Get banner as plain text for non-TTY environments."""
    return f"""
{BANNER_ASCII}
  Claude Project Manager
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Manage mono repos with multiple Claude Code
  projects. Share skills, agents, hooks, and
  rules across projects without duplication.

  ─────────────────────────────────────────

  Quick Start:
  $ cldpm init my-monorepo
  $ cldpm create project web-app
  $ cldpm create skill logging
  $ cldpm add skill:logging --to web-app

  ─────────────────────────────────────────

  ◆ Crafted by Transilience.ai
  ◆ Authored by Aman Agarwal
    github.com/amanagarwal041

  ─────────────────────────────────────────

  Docs:    https://cldpm.transilience.ai
  GitHub:  https://github.com/transilienceai/cldpm

  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
