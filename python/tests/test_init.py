"""Tests for cpm init command."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from cpm.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path


def test_init_current_directory(runner, temp_dir):
    """Test initializing in current directory."""
    with runner.isolated_filesystem(temp_dir=temp_dir):
        result = runner.invoke(cli, ["init"])

        assert result.exit_code == 0
        assert "Initialized CPM mono repo" in result.output

        # Check cpm.json exists
        assert Path("cpm.json").exists()
        with open("cpm.json") as f:
            config = json.load(f)
        assert "name" in config
        assert config["projectsDir"] == "projects"
        assert config["sharedDir"] == "shared"

        # Check directories exist
        assert Path("projects").is_dir()
        assert Path("shared/skills").is_dir()
        assert Path("shared/agents").is_dir()
        assert Path("shared/hooks").is_dir()
        assert Path("shared/rules").is_dir()
        assert Path(".cpm/templates").is_dir()

        # Check files exist
        assert Path("CLAUDE.md").exists()
        assert Path(".gitignore").exists()


def test_init_new_directory(runner, temp_dir):
    """Test initializing in a new directory."""
    with runner.isolated_filesystem(temp_dir=temp_dir):
        result = runner.invoke(cli, ["init", "my-monorepo"])

        assert result.exit_code == 0
        assert Path("my-monorepo/cpm.json").exists()
        assert Path("my-monorepo/projects").is_dir()
        assert Path("my-monorepo/shared").is_dir()


def test_init_with_name(runner, temp_dir):
    """Test initializing with custom name."""
    with runner.isolated_filesystem(temp_dir=temp_dir):
        result = runner.invoke(cli, ["init", "--name", "My Custom Repo"])

        assert result.exit_code == 0

        with open("cpm.json") as f:
            config = json.load(f)
        assert config["name"] == "My Custom Repo"


def test_init_already_exists(runner, temp_dir):
    """Test initializing when cpm.json already exists."""
    with runner.isolated_filesystem(temp_dir=temp_dir):
        # First init
        runner.invoke(cli, ["init"])

        # Second init should fail
        result = runner.invoke(cli, ["init"])

        assert result.exit_code == 1
        assert "already exists" in result.output


def test_init_existing_directory_without_flag(runner, temp_dir):
    """Test that init fails on non-empty directory without --existing flag."""
    with runner.isolated_filesystem(temp_dir=temp_dir):
        # Create some existing content
        Path("existing-file.txt").write_text("content")

        result = runner.invoke(cli, ["init"])

        assert result.exit_code == 1
        assert "not empty" in result.output
        assert "--existing" in result.output


def test_init_existing_directory_with_flag(runner, temp_dir):
    """Test initializing in an existing non-empty directory with --existing flag."""
    with runner.isolated_filesystem(temp_dir=temp_dir):
        # Create some existing content
        Path("existing-file.txt").write_text("content")
        Path("src").mkdir()
        Path("src/main.py").write_text("print('hello')")

        result = runner.invoke(cli, ["init", "--existing"])

        assert result.exit_code == 0
        assert "Initialized CPM mono repo" in result.output

        # Check CPM structure was created
        assert Path("cpm.json").exists()
        assert Path("projects").is_dir()
        assert Path("shared/skills").is_dir()

        # Check existing content is preserved
        assert Path("existing-file.txt").exists()
        assert Path("src/main.py").exists()


def test_init_existing_with_adopt_auto(runner, temp_dir):
    """Test --existing with --adopt-projects auto."""
    with runner.isolated_filesystem(temp_dir=temp_dir):
        # Create projects directory with some projects
        Path("projects").mkdir()
        Path("projects/app1").mkdir()
        Path("projects/app1/main.py").write_text("print('app1')")
        Path("projects/app2").mkdir()
        Path("projects/app2/package.json").write_text("{}")

        result = runner.invoke(cli, ["init", "--existing", "--adopt-projects", "auto"])

        assert result.exit_code == 0
        assert "Adopted" in result.output

        # Check projects were adopted
        assert Path("projects/app1/project.json").exists()
        assert Path("projects/app2/project.json").exists()


def test_init_existing_with_adopt_specific(runner, temp_dir):
    """Test --existing with specific project paths."""
    with runner.isolated_filesystem(temp_dir=temp_dir):
        # Create projects directory with projects
        Path("projects").mkdir()
        Path("projects/app1").mkdir()
        Path("projects/app1/main.py").write_text("print('app1')")
        Path("projects/app2").mkdir()
        Path("projects/app2/main.py").write_text("print('app2')")
        Path("projects/skip-me").mkdir()

        result = runner.invoke(
            cli, ["init", "--existing", "--adopt-projects", "projects/app1,projects/app2"]
        )

        assert result.exit_code == 0

        # Check only specified projects were adopted
        assert Path("projects/app1/project.json").exists()
        assert Path("projects/app2/project.json").exists()
        assert not Path("projects/skip-me/project.json").exists()


def test_init_existing_preserves_gitignore(runner, temp_dir):
    """Test that --existing appends to existing .gitignore."""
    with runner.isolated_filesystem(temp_dir=temp_dir):
        # Create existing .gitignore
        Path(".gitignore").write_text("node_modules/\n.env\n")

        result = runner.invoke(cli, ["init", "--existing"])

        assert result.exit_code == 0

        # Check .gitignore was updated, not replaced
        gitignore_content = Path(".gitignore").read_text()
        assert "node_modules/" in gitignore_content
        assert ".env" in gitignore_content
        assert "CPM Note" in gitignore_content


def test_init_custom_directories(runner, temp_dir):
    """Test init with custom projects and shared directories."""
    with runner.isolated_filesystem(temp_dir=temp_dir):
        result = runner.invoke(
            cli, ["init", "--projects-dir", "src", "--shared-dir", "common"]
        )

        assert result.exit_code == 0

        # Check custom directories were created
        assert Path("src").is_dir()
        assert Path("common/skills").is_dir()
        assert Path("common/agents").is_dir()

        # Check config has custom paths
        with open("cpm.json") as f:
            config = json.load(f)
        assert config["projectsDir"] == "src"
        assert config["sharedDir"] == "common"


def test_init_existing_already_initialized(runner, temp_dir):
    """Test --existing on already initialized repo shows warning."""
    with runner.isolated_filesystem(temp_dir=temp_dir):
        # First init
        runner.invoke(cli, ["init"])

        # Second init with --existing should warn but succeed
        result = runner.invoke(cli, ["init", "--existing"])

        assert result.exit_code == 0
        assert "already exists" in result.output
        assert "updating" in result.output
