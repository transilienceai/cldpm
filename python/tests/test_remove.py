"""Tests for cldpm remove command."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from cldpm.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


def create_shared_skill(name: str, dependencies: dict = None) -> None:
    """Create a shared skill for testing."""
    skill_path = Path(f"shared/skills/{name}")
    skill_path.mkdir(parents=True, exist_ok=True)
    (skill_path / "SKILL.md").write_text(f"# {name}\n\nTest skill.")

    metadata = {"name": name}
    if dependencies:
        metadata["dependencies"] = dependencies

    (skill_path / "skill.json").write_text(json.dumps(metadata, indent=2))


def test_remove_skill(runner, tmp_path):
    """Test removing a skill from a project."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        runner.invoke(cli, ["create", "project", "my-project"])
        create_shared_skill("test-skill")
        runner.invoke(cli, ["add", "skill:test-skill", "--to", "my-project"])

        result = runner.invoke(cli, ["remove", "skill:test-skill", "--from", "my-project"])

        assert result.exit_code == 0
        assert "Removed" in result.output

        # Verify skill was removed from project.json
        with open("projects/my-project/project.json") as f:
            config = json.load(f)
        assert "test-skill" not in config["dependencies"]["skills"]

        # Verify symlink was removed
        assert not Path("projects/my-project/.claude/skills/test-skill").exists()


def test_remove_nonexistent_component(runner, tmp_path):
    """Test removing a component that isn't in the project."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        runner.invoke(cli, ["create", "project", "my-project"])

        result = runner.invoke(cli, ["remove", "skill:nonexistent", "--from", "my-project"])

        assert result.exit_code == 1
        assert "not in project" in result.output.lower()


def test_remove_with_keep_deps(runner, tmp_path):
    """Test removing a component while keeping its dependencies."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        runner.invoke(cli, ["create", "project", "my-project"])

        # Create skill with dependency
        create_shared_skill("dep-skill")
        create_shared_skill("main-skill", {"skills": ["dep-skill"]})

        runner.invoke(cli, ["add", "skill:main-skill", "--to", "my-project"])

        result = runner.invoke(
            cli, ["remove", "skill:main-skill", "--from", "my-project", "--keep-deps"]
        )

        assert result.exit_code == 0

        # Verify main skill removed but dependency kept
        with open("projects/my-project/project.json") as f:
            config = json.load(f)
        assert "main-skill" not in config["dependencies"]["skills"]
        assert "dep-skill" in config["dependencies"]["skills"]


def test_remove_missing_project(runner, tmp_path):
    """Test removing from a nonexistent project."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])

        result = runner.invoke(cli, ["remove", "skill:test", "--from", "nonexistent"])

        assert result.exit_code == 1
        assert "not found" in result.output.lower()
