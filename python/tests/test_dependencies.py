"""Tests for component dependencies."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from cldpm.cli import cli
from cldpm.core.resolver import get_all_dependencies_for_component


@pytest.fixture
def runner():
    return CliRunner()


def create_shared_component(comp_type: str, name: str, dependencies: dict = None) -> None:
    """Create a shared component for testing."""
    comp_path = Path(f"shared/{comp_type}/{name}")
    comp_path.mkdir(parents=True, exist_ok=True)

    # Create content file
    singular = comp_type.rstrip("s").upper()
    (comp_path / f"{singular}.md").write_text(f"# {name}\n\nTest {singular.lower()}.")

    # Create metadata file
    singular_lower = comp_type.rstrip("s")
    metadata = {"name": name}
    if dependencies:
        metadata["dependencies"] = dependencies

    (comp_path / f"{singular_lower}.json").write_text(json.dumps(metadata, indent=2))


def test_add_with_dependencies(runner, tmp_path):
    """Test that adding a component also adds its dependencies."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        runner.invoke(cli, ["create", "project", "my-project"])

        # Create dependency skill
        create_shared_component("skills", "base-skill")

        # Create main skill that depends on base-skill
        create_shared_component("skills", "main-skill", {"skills": ["base-skill"]})

        result = runner.invoke(cli, ["add", "skill:main-skill", "--to", "my-project"])

        assert result.exit_code == 0
        assert "Added skills/main-skill" in result.output
        assert "base-skill" in result.output
        assert "dependency" in result.output.lower()

        # Verify both were added
        with open("projects/my-project/project.json") as f:
            config = json.load(f)
        assert "main-skill" in config["dependencies"]["skills"]
        assert "base-skill" in config["dependencies"]["skills"]


def test_add_with_no_deps_flag(runner, tmp_path):
    """Test that --no-deps skips dependency installation."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        runner.invoke(cli, ["create", "project", "my-project"])

        create_shared_component("skills", "base-skill")
        create_shared_component("skills", "main-skill", {"skills": ["base-skill"]})

        result = runner.invoke(
            cli, ["add", "skill:main-skill", "--to", "my-project", "--no-deps"]
        )

        assert result.exit_code == 0

        # Verify only main skill was added
        with open("projects/my-project/project.json") as f:
            config = json.load(f)
        assert "main-skill" in config["dependencies"]["skills"]
        assert "base-skill" not in config["dependencies"]["skills"]


def test_add_with_transitive_dependencies(runner, tmp_path):
    """Test that transitive dependencies are also added."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        runner.invoke(cli, ["create", "project", "my-project"])

        # Create chain: main -> middle -> base
        create_shared_component("skills", "base-skill")
        create_shared_component("skills", "middle-skill", {"skills": ["base-skill"]})
        create_shared_component("skills", "main-skill", {"skills": ["middle-skill"]})

        result = runner.invoke(cli, ["add", "skill:main-skill", "--to", "my-project"])

        assert result.exit_code == 0

        # Verify all three were added
        with open("projects/my-project/project.json") as f:
            config = json.load(f)
        assert "main-skill" in config["dependencies"]["skills"]
        assert "middle-skill" in config["dependencies"]["skills"]
        assert "base-skill" in config["dependencies"]["skills"]


def test_add_with_cross_type_dependencies(runner, tmp_path):
    """Test that dependencies across component types are added."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        runner.invoke(cli, ["create", "project", "my-project"])

        # Create skill dependency
        create_shared_component("skills", "helper-skill")

        # Create agent that depends on the skill
        create_shared_component("agents", "main-agent", {"skills": ["helper-skill"]})

        result = runner.invoke(cli, ["add", "agent:main-agent", "--to", "my-project"])

        assert result.exit_code == 0

        # Verify both were added
        with open("projects/my-project/project.json") as f:
            config = json.load(f)
        assert "main-agent" in config["dependencies"]["agents"]
        assert "helper-skill" in config["dependencies"]["skills"]


def test_resolve_component_dependencies(runner, tmp_path):
    """Test the dependency resolution function."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])

        create_shared_component("skills", "skill-a")
        create_shared_component("skills", "skill-b", {"skills": ["skill-a"]})
        create_shared_component("agents", "agent-x", {"skills": ["skill-b"]})

        repo_root = Path.cwd()
        deps = get_all_dependencies_for_component("agents", "agent-x", repo_root)

        assert "skill-b" in deps["skills"]
        assert "skill-a" in deps["skills"]


def test_dependency_already_exists(runner, tmp_path):
    """Test adding a component when its dependency is already in the project."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        runner.invoke(cli, ["create", "project", "my-project"])

        create_shared_component("skills", "base-skill")
        create_shared_component("skills", "main-skill", {"skills": ["base-skill"]})

        # First add the base skill
        runner.invoke(cli, ["add", "skill:base-skill", "--to", "my-project"])

        # Then add the main skill (base-skill already exists)
        result = runner.invoke(cli, ["add", "skill:main-skill", "--to", "my-project"])

        assert result.exit_code == 0

        # Verify both exist but base-skill wasn't duplicated
        with open("projects/my-project/project.json") as f:
            config = json.load(f)
        assert config["dependencies"]["skills"].count("base-skill") == 1
        assert config["dependencies"]["skills"].count("main-skill") == 1
