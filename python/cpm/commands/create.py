"""Implementation of cpm create command."""

from pathlib import Path
from typing import Optional

import click
from jinja2 import Environment, PackageLoader

from ..schemas import ProjectConfig, ProjectDependencies
from ..core.config import load_cpm_config, save_project_config
from ..core.linker import sync_project_links
from ..utils.fs import ensure_dir, find_repo_root
from ..utils.output import print_success, print_error, print_dir_tree, console


@click.group()
def create() -> None:
    """Create new projects or components."""
    pass


@create.command()
@click.argument("name")
@click.option("--description", "-d", help="Project description")
@click.option("--skills", "-s", help="Comma-separated list of shared skills to add")
@click.option("--agents", "-a", help="Comma-separated list of shared agents to add")
def project(
    name: str,
    description: Optional[str],
    skills: Optional[str],
    agents: Optional[str],
) -> None:
    """Create a new project in the mono repo.

    Creates a project with the standard structure for Claude Code, including
    directories for both shared (symlinked) and local (project-specific)
    components.

    \b
    Structure created:
      project.json     - Project manifest (tracks shared dependencies)
      CLAUDE.md        - Project instructions
      .claude/         - Components directory
        skills/        - Skills (shared symlinks + local)
        agents/        - Agents (shared symlinks + local)
        hooks/         - Hooks (shared symlinks + local)
        rules/         - Rules (shared symlinks + local)
      outputs/         - Project outputs

    \b
    Examples:
      cpm create project my-app
      cpm create project my-app -d "My application"
      cpm create project my-app --skills skill1,skill2
      cpm create project my-app -s skill1 -a agent1
    """
    # Find repo root
    repo_root = find_repo_root()
    if repo_root is None:
        print_error("Not in a CPM mono repo. Run 'cpm init' first.")
        raise SystemExit(1)

    # Load config
    cpm_config = load_cpm_config(repo_root)

    # Create project directory
    project_path = repo_root / cpm_config.projects_dir / name

    if project_path.exists():
        print_error(f"Project already exists: {name}")
        raise SystemExit(1)

    ensure_dir(project_path)

    # Parse dependencies
    deps = ProjectDependencies()
    if skills:
        deps.skills = [s.strip() for s in skills.split(",") if s.strip()]
    if agents:
        deps.agents = [a.strip() for a in agents.split(",") if a.strip()]

    # Create project config
    project_config = ProjectConfig(
        name=name,
        description=description,
        dependencies=deps,
    )
    save_project_config(project_config, project_path)

    # Create .claude directory structure
    claude_dir = project_path / ".claude"
    ensure_dir(claude_dir)
    ensure_dir(claude_dir / "skills")
    ensure_dir(claude_dir / "agents")
    ensure_dir(claude_dir / "hooks")
    ensure_dir(claude_dir / "rules")

    # Create settings.json placeholder
    (claude_dir / "settings.json").write_text("{}\n")

    # Create outputs directory
    ensure_dir(project_path / "outputs")

    # Create CLAUDE.md from template
    env = Environment(loader=PackageLoader("cpm", "templates"))
    template = env.get_template("CLAUDE.md.j2")
    claude_md = template.render(
        project_name=name,
        description=description or "",
    )
    (project_path / "CLAUDE.md").write_text(claude_md)

    print_success(f"Created project: {name}")

    # Sync symlinks if dependencies were specified
    if deps.skills or deps.agents:
        result = sync_project_links(project_path, repo_root)
        if result["created"]:
            console.print(f"  Linked: {', '.join(result['created'])}")
        if result["missing"]:
            console.print(f"  [yellow]Missing:[/yellow] {', '.join(result['missing'])}")

    console.print()
    print_dir_tree(project_path, max_depth=2)
