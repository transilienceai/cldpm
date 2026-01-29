"""Tests for cpm get command."""

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


def create_local_skill(project_name: str, skill_name: str) -> None:
    """Create a local (project-specific) skill for testing."""
    skill_path = Path(f"projects/{project_name}/.claude/skills/{skill_name}")
    skill_path.mkdir(parents=True, exist_ok=True)
    (skill_path / "SKILL.md").write_text(f"# {skill_name}\n\nLocal skill.")


def test_get_project_tree(runner, tmp_path):
    """Test getting project info in tree format."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        runner.invoke(cli, ["create", "project", "my-project"])

        result = runner.invoke(cli, ["get", "my-project"])

        assert result.exit_code == 0
        assert "my-project" in result.output


def test_get_project_json(runner, tmp_path):
    """Test getting project info in JSON format."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        runner.invoke(cli, ["create", "project", "my-project"])

        result = runner.invoke(cli, ["get", "my-project", "--format", "json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["name"] == "my-project"
        assert "path" in data
        assert "config" in data
        assert "shared" in data
        assert "local" in data


def test_get_project_with_shared_dependencies(runner, tmp_path):
    """Test getting project with resolved shared dependencies."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        runner.invoke(cli, ["create", "project", "my-project"])
        create_shared_skill("test-skill")
        runner.invoke(cli, ["add", "skill:test-skill", "--to", "my-project"])

        result = runner.invoke(cli, ["get", "my-project", "--format", "json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data["shared"]["skills"]) == 1
        assert data["shared"]["skills"][0]["name"] == "test-skill"
        assert data["shared"]["skills"][0]["type"] == "shared"
        assert "SKILL.md" in data["shared"]["skills"][0]["files"]


def test_get_project_with_local_components(runner, tmp_path):
    """Test getting project with local (project-specific) components."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        runner.invoke(cli, ["create", "project", "my-project"])
        create_local_skill("my-project", "local-skill")

        result = runner.invoke(cli, ["get", "my-project", "--format", "json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data["local"]["skills"]) == 1
        assert data["local"]["skills"][0]["name"] == "local-skill"
        assert data["local"]["skills"][0]["type"] == "local"


def test_get_project_with_both_shared_and_local(runner, tmp_path):
    """Test getting project with both shared and local components."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        runner.invoke(cli, ["create", "project", "my-project"])
        create_shared_skill("shared-skill")
        runner.invoke(cli, ["add", "skill:shared-skill", "--to", "my-project"])
        create_local_skill("my-project", "local-skill")

        result = runner.invoke(cli, ["get", "my-project", "--format", "json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data["shared"]["skills"]) == 1
        assert len(data["local"]["skills"]) == 1
        assert data["shared"]["skills"][0]["name"] == "shared-skill"
        assert data["local"]["skills"][0]["name"] == "local-skill"


def test_get_project_by_path(runner, tmp_path):
    """Test getting project by path."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        runner.invoke(cli, ["create", "project", "my-project"])

        result = runner.invoke(
            cli, ["get", "projects/my-project", "--format", "json"]
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["name"] == "my-project"


def test_get_missing_project(runner, tmp_path):
    """Test getting a project that doesn't exist."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])

        result = runner.invoke(cli, ["get", "nonexistent"])

        assert result.exit_code == 1
        assert "not found" in result.output.lower()


def test_get_download_local_default_output(runner, tmp_path):
    """Test downloading a local project to default output directory."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        runner.invoke(cli, ["create", "project", "my-project"])

        result = runner.invoke(cli, ["get", "my-project", "--download"])

        assert result.exit_code == 0
        assert "Downloaded to" in result.output

        # Check that the project was copied to ./my-project
        target = Path("my-project")
        assert target.exists()
        assert (target / "project.json").exists()
        assert (target / "CLAUDE.md").exists()
        assert (target / ".claude").is_dir()


def test_get_download_local_custom_output(runner, tmp_path):
    """Test downloading a local project to custom output directory."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        runner.invoke(cli, ["create", "project", "my-project"])

        result = runner.invoke(
            cli, ["get", "my-project", "-d", "-o", "./custom-output"]
        )

        assert result.exit_code == 0
        assert "Downloaded to" in result.output

        # Check that the project was copied to custom directory
        target = Path("custom-output")
        assert target.exists()
        assert (target / "project.json").exists()
        assert (target / "CLAUDE.md").exists()


def test_get_download_with_shared_components(runner, tmp_path):
    """Test that shared components are copied as actual files, not symlinks."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        runner.invoke(cli, ["create", "project", "my-project"])
        create_shared_skill("test-skill")
        runner.invoke(cli, ["add", "skill:test-skill", "--to", "my-project"])

        result = runner.invoke(cli, ["get", "my-project", "--download"])

        assert result.exit_code == 0

        # Check that shared skill was copied (not symlinked)
        target = Path("my-project")
        skill_path = target / ".claude" / "skills" / "test-skill"
        assert skill_path.exists()
        assert skill_path.is_dir()
        assert not skill_path.is_symlink()  # Must be real directory, not symlink
        assert (skill_path / "SKILL.md").exists()
        assert (skill_path / "skill.json").exists()


def test_get_download_with_local_components(runner, tmp_path):
    """Test that local components are preserved in download."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        runner.invoke(cli, ["create", "project", "my-project"])
        create_local_skill("my-project", "local-skill")

        result = runner.invoke(cli, ["get", "my-project", "--download"])

        assert result.exit_code == 0

        # Check that local skill was copied
        target = Path("my-project")
        skill_path = target / ".claude" / "skills" / "local-skill"
        assert skill_path.exists()
        assert (skill_path / "SKILL.md").exists()


def test_get_download_with_both_shared_and_local(runner, tmp_path):
    """Test downloading project with both shared and local components."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        runner.invoke(cli, ["create", "project", "my-project"])
        create_shared_skill("shared-skill")
        runner.invoke(cli, ["add", "skill:shared-skill", "--to", "my-project"])
        create_local_skill("my-project", "local-skill")

        result = runner.invoke(cli, ["get", "my-project", "--download"])

        assert result.exit_code == 0
        assert "Shared:" in result.output
        assert "Local:" in result.output

        # Check both components exist
        target = Path("my-project")
        shared_skill = target / ".claude" / "skills" / "shared-skill"
        local_skill = target / ".claude" / "skills" / "local-skill"
        assert shared_skill.exists()
        assert not shared_skill.is_symlink()
        assert local_skill.exists()


def test_get_download_target_exists_error(runner, tmp_path):
    """Test error when download target directory already exists."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        runner.invoke(cli, ["create", "project", "my-project"])

        # Create a directory that would conflict
        Path("my-project").mkdir()

        result = runner.invoke(cli, ["get", "my-project", "--download"])

        assert result.exit_code == 1
        assert "already exists" in result.output.lower()
