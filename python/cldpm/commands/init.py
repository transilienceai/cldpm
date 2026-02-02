"""Implementation of cldpm init command."""

from pathlib import Path
from typing import Optional

import click
from jinja2 import Environment, PackageLoader

from ..schemas import CldpmConfig, ProjectConfig, ProjectDependencies
from ..core.config import save_cldpm_config, save_project_config
from ..utils.fs import ensure_dir
from ..utils.output import print_success, print_error, print_warning, print_dir_tree, console
from ..ai_rules import create_ai_rules, append_to_claude_md


@click.command()
@click.argument("directory", required=False, default=".")
@click.option("--name", "-n", help="Name for the mono repo")
@click.option(
    "--existing",
    "-e",
    is_flag=True,
    help="Initialize in an existing directory without overwriting files",
)
@click.option(
    "--adopt-projects",
    "-a",
    "adopt_projects",
    help="Adopt existing directories as projects (comma-separated paths or 'auto' to detect)",
)
@click.option(
    "--projects-dir",
    "-p",
    "projects_dir",
    default="projects",
    help="Directory for projects (default: projects)",
)
@click.option(
    "--shared-dir",
    "-s",
    "shared_dir",
    default="shared",
    help="Directory for shared components (default: shared)",
)
def init(
    directory: str,
    name: Optional[str],
    existing: bool,
    adopt_projects: Optional[str],
    projects_dir: str,
    shared_dir: str,
) -> None:
    """Initialize a new CLDPM mono repo.

    Creates the directory structure and configuration files for managing
    multiple Claude Code projects with shared and local components.

    \b
    Structure created:
      shared/          - Shared components (skills, agents, hooks, rules)
      projects/        - Individual projects
      cldpm.json       - Mono repo configuration
      CLAUDE.md        - Root instructions

    \b
    Examples:
      cldpm init                              # Current directory
      cldpm init my-monorepo                  # New directory
      cldpm init --name "My Repo"             # Custom name
      cldpm init -e                           # Existing repo, don't overwrite
      cldpm init -e --adopt-projects auto     # Auto-detect existing projects
      cldpm init -e -a "app,api"              # Adopt specific projects
      cldpm init -p src -s common             # Custom directory names
    """
    # Resolve directory
    repo_root = Path(directory).resolve()

    # Check if already initialized
    if (repo_root / "cldpm.json").exists():
        if existing:
            print_warning(f"CLDPM repo already exists at {repo_root}, updating...")
        else:
            print_error(f"CLDPM repo already exists at {repo_root}")
            raise SystemExit(1)

    # Check if directory exists and has content (for non-existing mode)
    if not existing and repo_root.exists() and any(repo_root.iterdir()):
        print_error(
            f"Directory {repo_root} is not empty. Use --existing to initialize an existing repo."
        )
        raise SystemExit(1)

    # Determine repo name
    if name is None:
        name = repo_root.name

    # Create directory if needed
    ensure_dir(repo_root)

    # Create config
    config = CldpmConfig(
        name=name,
        projectsDir=projects_dir,
        sharedDir=shared_dir,
    )
    save_cldpm_config(config, repo_root)

    # Create directory structure
    dirs_to_create = [
        f"{shared_dir}/skills",
        f"{shared_dir}/agents",
        f"{shared_dir}/hooks",
        f"{shared_dir}/rules",
        projects_dir,
        ".cldpm/templates",
    ]

    for dir_path in dirs_to_create:
        ensure_dir(repo_root / dir_path)

    # Create templates using Jinja2
    env = Environment(loader=PackageLoader("cldpm", "templates"))

    # Create root CLAUDE.md (only if it doesn't exist or not in existing mode)
    claude_md_path = repo_root / "CLAUDE.md"
    if not existing or not claude_md_path.exists():
        template = env.get_template("ROOT_CLAUDE.md.j2")
        claude_md = template.render(repo_name=name)
        claude_md_path.write_text(claude_md)

    # Create/update .gitignore
    gitignore_path = repo_root / ".gitignore"
    if not existing or not gitignore_path.exists():
        template = env.get_template("gitignore.j2")
        gitignore = template.render()
        gitignore_path.write_text(gitignore)
    elif existing and gitignore_path.exists():
        # Append CLDPM-specific entries if not already present
        _update_gitignore(gitignore_path)

    # Create AI rules files for various AI coding assistants
    create_ai_rules(repo_root, name, projects_dir, shared_dir, existing)

    # Append CLDPM section to CLAUDE.md if it exists and doesn't have it
    if existing:
        append_to_claude_md(claude_md_path)

    print_success(f"Initialized CLDPM mono repo: {name}")

    # Adopt existing projects if requested
    if adopt_projects:
        adopted = _adopt_projects(repo_root, adopt_projects, projects_dir, env)
        if adopted:
            console.print(f"  Adopted {len(adopted)} project(s): {', '.join(adopted)}")

    console.print()
    print_dir_tree(repo_root, max_depth=2)


def _update_gitignore(gitignore_path: Path) -> None:
    """Update existing .gitignore with CLDPM-specific note."""
    existing_content = gitignore_path.read_text()

    # Check if CLDPM note already exists
    if "CLDPM Note" in existing_content or "CLDPM shared components" in existing_content:
        return

    cldpm_note = """
# CLDPM Note: Shared component symlinks are managed per-directory
# Each .claude/{skills,agents,hooks,rules}/ has its own .gitignore
# that only ignores symlinked shared components.
# Project-specific components in those directories ARE committed.
"""

    # Append CLDPM note
    with open(gitignore_path, "a") as f:
        f.write(cldpm_note)


def _adopt_projects(
    repo_root: Path,
    adopt_projects: str,
    projects_dir: str,
    env: Environment,
) -> list[str]:
    """Adopt existing directories as CLDPM projects.

    Args:
        repo_root: Path to the repo root.
        adopt_projects: Comma-separated project paths or 'auto'.
        projects_dir: Directory containing projects.
        env: Jinja2 environment for templates.

    Returns:
        List of adopted project names.
    """
    adopted = []
    projects_path = repo_root / projects_dir

    if adopt_projects.lower() == "auto":
        # Auto-detect: look for directories in projects_dir or repo root
        candidates = []

        # Check projects directory
        if projects_path.exists():
            candidates.extend(
                [d for d in projects_path.iterdir() if d.is_dir() and not d.name.startswith(".")]
            )

        # If no projects_dir or it's empty, check repo root for potential projects
        if not candidates:
            for item in repo_root.iterdir():
                if (
                    item.is_dir()
                    and not item.name.startswith(".")
                    and item.name not in ["shared", "projects", ".cldpm", "node_modules", "__pycache__", "venv", ".venv"]
                ):
                    # Check if it looks like a project (has code or package files)
                    if _looks_like_project(item):
                        candidates.append(item)
    else:
        # Explicit project paths
        candidates = []
        for proj_path in adopt_projects.split(","):
            proj_path = proj_path.strip()
            if not proj_path:
                continue

            full_path = repo_root / proj_path
            if full_path.exists() and full_path.is_dir():
                candidates.append(full_path)
            else:
                print_warning(f"Project path not found: {proj_path}")

    # Adopt each candidate
    for candidate in candidates:
        project_name = candidate.name

        # Skip if already has project.json
        if (candidate / "project.json").exists():
            print_warning(f"Skipping {project_name}: already has project.json")
            continue

        # Create project.json
        project_config = ProjectConfig(
            name=project_name,
            description=f"Adopted project: {project_name}",
            dependencies=ProjectDependencies(),
        )

        # If project is not in projects_dir, we need to handle it
        if candidate.parent != projects_path:
            # Move to projects directory or create a reference
            target_path = projects_path / project_name
            if not target_path.exists():
                # Create the project in projects_dir with a reference
                ensure_dir(target_path)
                save_project_config(project_config, target_path)
                _setup_project_structure(target_path, env, project_name)

                # Note: The original directory stays in place
                # User may want to move files manually or set up differently
                print_warning(
                    f"Created project entry for {project_name}. "
                    f"Original files remain at {candidate.relative_to(repo_root)}"
                )
            adopted.append(project_name)
        else:
            # Project is already in projects_dir
            save_project_config(project_config, candidate)
            _setup_project_structure(candidate, env, project_name)
            adopted.append(project_name)

    return adopted


def _looks_like_project(path: Path) -> bool:
    """Check if a directory looks like a project.

    Looks for common project indicators like package files, source directories, etc.
    """
    indicators = [
        "package.json",
        "pyproject.toml",
        "setup.py",
        "Cargo.toml",
        "go.mod",
        "pom.xml",
        "build.gradle",
        "Makefile",
        "CMakeLists.txt",
        "src",
        "lib",
        "app",
        "main.py",
        "index.js",
        "index.ts",
        "CLAUDE.md",
        ".claude",
    ]

    for indicator in indicators:
        if (path / indicator).exists():
            return True

    return False


def _setup_project_structure(
    project_path: Path,
    env: Environment,
    project_name: str,
) -> None:
    """Set up the standard CLDPM project structure."""
    # Create .claude directory structure
    claude_dir = project_path / ".claude"
    ensure_dir(claude_dir)
    ensure_dir(claude_dir / "skills")
    ensure_dir(claude_dir / "agents")
    ensure_dir(claude_dir / "hooks")
    ensure_dir(claude_dir / "rules")

    # Create settings.json if it doesn't exist
    settings_path = claude_dir / "settings.json"
    if not settings_path.exists():
        settings_path.write_text("{}\n")

    # Create outputs directory
    ensure_dir(project_path / "outputs")

    # Create CLAUDE.md from template if it doesn't exist
    claude_md_path = project_path / "CLAUDE.md"
    if not claude_md_path.exists():
        template = env.get_template("CLAUDE.md.j2")
        claude_md = template.render(
            project_name=project_name,
            description="",
        )
        claude_md_path.write_text(claude_md)
