"""Tests for cpm sync command."""

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


def test_sync_single_project(runner, tmp_path):
    """Test syncing a single project."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        runner.invoke(cli, ["create", "project", "my-project"])
        create_shared_skill("test-skill")
        runner.invoke(cli, ["add", "skill:test-skill", "--to", "my-project"])

        # Remove symlink manually
        symlink = Path("projects/my-project/.claude/skills/test-skill")
        symlink.unlink()
        assert not symlink.exists()

        # Sync should restore it
        result = runner.invoke(cli, ["sync", "my-project"])

        assert result.exit_code == 0
        assert "synced" in result.output
        assert symlink.is_symlink()


def test_sync_all_projects(runner, tmp_path):
    """Test syncing all projects."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        runner.invoke(cli, ["create", "project", "project1"])
        runner.invoke(cli, ["create", "project", "project2"])
        create_shared_skill("test-skill")
        runner.invoke(cli, ["add", "skill:test-skill", "--to", "project1"])
        runner.invoke(cli, ["add", "skill:test-skill", "--to", "project2"])

        # Remove symlinks manually
        for project in ["project1", "project2"]:
            symlink = Path(f"projects/{project}/.claude/skills/test-skill")
            symlink.unlink()
            assert not symlink.exists()

        # Sync all should restore them
        result = runner.invoke(cli, ["sync", "--all"])

        assert result.exit_code == 0
        for project in ["project1", "project2"]:
            symlink = Path(f"projects/{project}/.claude/skills/test-skill")
            assert symlink.is_symlink()


def test_sync_missing_component(runner, tmp_path):
    """Test syncing when a referenced component is missing."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        runner.invoke(cli, ["create", "project", "my-project"])
        create_shared_skill("test-skill")
        runner.invoke(cli, ["add", "skill:test-skill", "--to", "my-project"])

        # Delete the shared skill
        import shutil
        shutil.rmtree("shared/skills/test-skill")

        result = runner.invoke(cli, ["sync", "my-project"])

        # Should warn about missing component
        assert "missing" in result.output.lower()


def test_sync_missing_project(runner, tmp_path):
    """Test syncing a project that doesn't exist."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])

        result = runner.invoke(cli, ["sync", "nonexistent"])

        assert result.exit_code == 1
        assert "not found" in result.output.lower()


def test_sync_no_args(runner, tmp_path):
    """Test sync without project name or --all flag."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])

        result = runner.invoke(cli, ["sync"])

        assert result.exit_code == 1
        assert "Specify a project name" in result.output
