"""Tests for cpm add command."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from cpm.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


def create_shared_skill(name: str) -> None:
    """Create a shared skill for testing."""
    skill_path = Path(f"shared/skills/{name}")
    skill_path.mkdir(parents=True, exist_ok=True)
    (skill_path / "SKILL.md").write_text(f"# {name}\n\nTest skill.")
    (skill_path / "skill.json").write_text(
        json.dumps({"name": name, "version": "1.0.0"})
    )


def test_add_skill_explicit_type(runner, tmp_path):
    """Test adding a skill with explicit type."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        runner.invoke(cli, ["create", "project", "my-project"])
        create_shared_skill("test-skill")

        result = runner.invoke(cli, ["add", "skill:test-skill", "--to", "my-project"])

        assert result.exit_code == 0
        assert "Added skills/test-skill to my-project" in result.output

        # Check project.json was updated
        with open("projects/my-project/project.json") as f:
            config = json.load(f)
        assert "test-skill" in config["dependencies"]["skills"]

        # Check symlink was created
        symlink_path = Path("projects/my-project/.claude/skills/test-skill")
        assert symlink_path.is_symlink()


def test_add_skill_auto_detect(runner, tmp_path):
    """Test adding a skill with auto-detection."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        runner.invoke(cli, ["create", "project", "my-project"])
        create_shared_skill("auto-skill")

        result = runner.invoke(cli, ["add", "auto-skill", "--to", "my-project"])

        assert result.exit_code == 0
        assert "Added skills/auto-skill to my-project" in result.output


def test_add_missing_component(runner, tmp_path):
    """Test adding a component that doesn't exist."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        runner.invoke(cli, ["create", "project", "my-project"])

        result = runner.invoke(cli, ["add", "skill:nonexistent", "--to", "my-project"])

        assert result.exit_code == 1
        assert "not found" in result.output


def test_add_missing_project(runner, tmp_path):
    """Test adding to a project that doesn't exist."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        create_shared_skill("test-skill")

        result = runner.invoke(cli, ["add", "skill:test-skill", "--to", "nonexistent"])

        assert result.exit_code == 1
        assert "Project not found" in result.output


def test_add_duplicate(runner, tmp_path):
    """Test adding the same component twice."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        runner.invoke(cli, ["create", "project", "my-project"])
        create_shared_skill("test-skill")

        runner.invoke(cli, ["add", "skill:test-skill", "--to", "my-project"])
        result = runner.invoke(cli, ["add", "skill:test-skill", "--to", "my-project"])

        assert "already in project" in result.output
