"""Tests for cldpm clone command."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from cldpm.cli import cli


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


def test_clone_project(runner, tmp_path):
    """Test cloning a project."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        runner.invoke(cli, ["create", "project", "my-project"])
        create_shared_skill("test-skill")
        runner.invoke(cli, ["add", "skill:test-skill", "--to", "my-project"])

        result = runner.invoke(cli, ["clone", "my-project", "cloned-project"])

        assert result.exit_code == 0
        assert "Cloned my-project" in result.output

        # Check cloned project structure
        cloned = Path("cloned-project")
        assert cloned.is_dir()
        assert (cloned / "project.json").exists()
        assert (cloned / "CLAUDE.md").exists()
        assert (cloned / ".claude").is_dir()

        # Check skill was copied (not symlinked)
        skill_path = cloned / ".claude/skills/test-skill"
        assert skill_path.is_dir()
        assert not skill_path.is_symlink()
        assert (skill_path / "SKILL.md").exists()


def test_clone_with_include_shared(runner, tmp_path):
    """Test cloning with --include-shared flag."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        runner.invoke(cli, ["create", "project", "my-project"])
        create_shared_skill("test-skill")

        result = runner.invoke(
            cli, ["clone", "my-project", "cloned-project", "--include-shared"]
        )

        assert result.exit_code == 0

        # Check shared directory was copied
        cloned = Path("cloned-project")
        assert (cloned / "shared").is_dir()
        assert (cloned / "shared/skills/test-skill").is_dir()
        assert (cloned / "cldpm.json").exists()


def test_clone_target_exists(runner, tmp_path):
    """Test cloning to an existing directory."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        runner.invoke(cli, ["create", "project", "my-project"])
        Path("cloned-project").mkdir()

        result = runner.invoke(cli, ["clone", "my-project", "cloned-project"])

        assert result.exit_code == 1
        assert "already exists" in result.output


def test_clone_missing_project(runner, tmp_path):
    """Test cloning a project that doesn't exist."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])

        result = runner.invoke(cli, ["clone", "nonexistent", "cloned-project"])

        assert result.exit_code == 1
        assert "not found" in result.output.lower()
