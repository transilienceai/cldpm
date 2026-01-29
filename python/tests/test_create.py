"""Tests for cpm create command."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from cpm.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def initialized_repo(runner, tmp_path):
    """Create an initialized CPM repo for testing."""
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        runner.invoke(cli, ["init"])
        yield Path(td)


def test_create_project(runner, tmp_path):
    """Test creating a new project."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        result = runner.invoke(cli, ["create", "project", "my-audit"])

        assert result.exit_code == 0
        assert "Created project: my-audit" in result.output

        # Check project structure
        project_path = Path("projects/my-audit")
        assert project_path.is_dir()
        assert (project_path / "project.json").exists()
        assert (project_path / "CLAUDE.md").exists()
        assert (project_path / ".claude").is_dir()
        assert (project_path / ".claude/settings.json").exists()
        assert (project_path / "outputs").is_dir()

        # Check project.json content
        with open(project_path / "project.json") as f:
            config = json.load(f)
        assert config["name"] == "my-audit"
        assert "dependencies" in config


def test_create_project_with_description(runner, tmp_path):
    """Test creating a project with description."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        result = runner.invoke(
            cli, ["create", "project", "my-audit", "-d", "Security audit project"]
        )

        assert result.exit_code == 0

        with open("projects/my-audit/project.json") as f:
            config = json.load(f)
        assert config["description"] == "Security audit project"


def test_create_project_with_skills(runner, tmp_path):
    """Test creating a project with initial skills."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        result = runner.invoke(
            cli, ["create", "project", "my-audit", "--skills", "skill1,skill2"]
        )

        assert result.exit_code == 0

        with open("projects/my-audit/project.json") as f:
            config = json.load(f)
        assert config["dependencies"]["skills"] == ["skill1", "skill2"]


def test_create_project_already_exists(runner, tmp_path):
    """Test creating a project that already exists."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        runner.invoke(cli, ["create", "project", "my-audit"])

        result = runner.invoke(cli, ["create", "project", "my-audit"])

        assert result.exit_code == 1
        assert "already exists" in result.output


def test_create_project_not_in_repo(runner, tmp_path):
    """Test creating a project outside a CPM repo."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(cli, ["create", "project", "my-audit"])

        assert result.exit_code == 1
        assert "Not in a CPM mono repo" in result.output
