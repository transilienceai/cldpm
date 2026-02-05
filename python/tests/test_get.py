"""Tests for cldpm get command."""

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


def test_get_json_output_has_required_fields(runner, tmp_path):
    """Test that JSON output contains all required fields for display."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        runner.invoke(cli, ["create", "project", "my-project"])
        create_shared_skill("test-skill")
        runner.invoke(cli, ["add", "skill:test-skill", "--to", "my-project"])
        create_local_skill("my-project", "local-skill")

        result = runner.invoke(cli, ["get", "my-project", "--format", "json"])

        assert result.exit_code == 0
        data = json.loads(result.output)

        # Check shared component has required fields
        shared_skill = data["shared"]["skills"][0]
        assert "name" in shared_skill
        assert "type" in shared_skill
        assert "sourcePath" in shared_skill
        assert "files" in shared_skill
        assert shared_skill["type"] == "shared"
        assert "shared/skills/test-skill" in shared_skill["sourcePath"]

        # Check local component has required fields
        local_skill = data["local"]["skills"][0]
        assert "name" in local_skill
        assert "type" in local_skill
        assert "sourcePath" in local_skill
        assert "files" in local_skill
        assert local_skill["type"] == "local"


def test_get_shared_component_files_list(runner, tmp_path):
    """Test that shared components include correct files list."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        runner.invoke(cli, ["create", "project", "my-project"])
        create_shared_skill("test-skill")
        runner.invoke(cli, ["add", "skill:test-skill", "--to", "my-project"])

        result = runner.invoke(cli, ["get", "my-project", "--format", "json"])

        assert result.exit_code == 0
        data = json.loads(result.output)

        shared_skill = data["shared"]["skills"][0]
        assert "SKILL.md" in shared_skill["files"]
        assert "skill.json" in shared_skill["files"]


def test_get_local_component_files_list(runner, tmp_path):
    """Test that local components include correct files list."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        runner.invoke(cli, ["create", "project", "my-project"])
        create_local_skill("my-project", "local-skill")

        result = runner.invoke(cli, ["get", "my-project", "--format", "json"])

        assert result.exit_code == 0
        data = json.loads(result.output)

        local_skill = data["local"]["skills"][0]
        assert "SKILL.md" in local_skill["files"]


class TestBuildSparseResult:
    """Tests for _build_sparse_result function used in remote get."""

    def test_build_sparse_result_shared_components(self, tmp_path):
        """Test that _build_sparse_result includes correct fields for shared components."""
        from cldpm.commands.get import _build_sparse_result

        # Set up mock temp directory structure
        project_path = "projects/test-project"
        shared_dir = "shared"

        # Create project directory
        (tmp_path / project_path).mkdir(parents=True)
        (tmp_path / project_path / "project.json").write_text('{"name": "test-project"}')

        # Create shared skill
        skill_dir = tmp_path / shared_dir / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# My Skill")
        (skill_dir / "skill.json").write_text('{"name": "my-skill"}')

        project_config = {"name": "test-project"}
        dependencies = {"skills": ["my-skill"], "agents": [], "hooks": [], "rules": []}

        result = _build_sparse_result(
            tmp_path,
            "test-project",
            project_path,
            shared_dir,
            project_config,
            dependencies,
            "owner/repo",
            "https://github.com/owner/repo.git",
            None,
        )

        # Check result structure
        assert result["name"] == "test-project"
        assert "shared" in result
        assert "local" in result

        # Check shared skill has all required fields
        shared_skills = result["shared"]["skills"]
        assert len(shared_skills) == 1
        skill = shared_skills[0]
        assert skill["name"] == "my-skill"
        assert skill["type"] == "shared"
        assert skill["sourcePath"] == "shared/skills/my-skill"
        assert "SKILL.md" in skill["files"]
        assert "skill.json" in skill["files"]

    def test_build_sparse_result_local_components(self, tmp_path):
        """Test that _build_sparse_result includes correct fields for local components."""
        from cldpm.commands.get import _build_sparse_result

        # Set up mock temp directory structure
        project_path = "projects/test-project"
        shared_dir = "shared"

        # Create project directory with local skill
        project_dir = tmp_path / project_path
        project_dir.mkdir(parents=True)
        (project_dir / "project.json").write_text('{"name": "test-project"}')

        local_skill_dir = project_dir / ".claude" / "skills" / "local-skill"
        local_skill_dir.mkdir(parents=True)
        (local_skill_dir / "SKILL.md").write_text("# Local Skill")

        project_config = {"name": "test-project"}
        dependencies = {"skills": [], "agents": [], "hooks": [], "rules": []}

        result = _build_sparse_result(
            tmp_path,
            "test-project",
            project_path,
            shared_dir,
            project_config,
            dependencies,
            "owner/repo",
            "https://github.com/owner/repo.git",
            None,
        )

        # Check local skill has all required fields
        local_skills = result["local"]["skills"]
        assert len(local_skills) == 1
        skill = local_skills[0]
        assert skill["name"] == "local-skill"
        assert skill["type"] == "local"
        assert skill["sourcePath"] == ".claude/skills/local-skill"
        assert "SKILL.md" in skill["files"]

    def test_build_sparse_result_excludes_symlinks(self, tmp_path):
        """Test that _build_sparse_result excludes symlinks from local components."""
        from cldpm.commands.get import _build_sparse_result
        import os

        # Set up mock temp directory structure
        project_path = "projects/test-project"
        shared_dir = "shared"

        # Create project directory
        project_dir = tmp_path / project_path
        project_dir.mkdir(parents=True)
        (project_dir / "project.json").write_text('{"name": "test-project"}')

        # Create shared skill (the symlink target)
        shared_skill = tmp_path / shared_dir / "skills" / "shared-skill"
        shared_skill.mkdir(parents=True)
        (shared_skill / "SKILL.md").write_text("# Shared Skill")

        # Create .claude/skills directory with a symlink
        local_skills_dir = project_dir / ".claude" / "skills"
        local_skills_dir.mkdir(parents=True)
        symlink_path = local_skills_dir / "shared-skill"
        os.symlink(shared_skill, symlink_path)

        # Also create a real local skill
        real_local = local_skills_dir / "real-local"
        real_local.mkdir()
        (real_local / "SKILL.md").write_text("# Real Local")

        project_config = {"name": "test-project"}
        dependencies = {"skills": [], "agents": [], "hooks": [], "rules": []}

        result = _build_sparse_result(
            tmp_path,
            "test-project",
            project_path,
            shared_dir,
            project_config,
            dependencies,
            "owner/repo",
            "https://github.com/owner/repo.git",
            None,
        )

        # Check that only real local skill is included (symlink excluded)
        local_skills = result["local"]["skills"]
        assert len(local_skills) == 1
        assert local_skills[0]["name"] == "real-local"

    def test_build_sparse_result_excludes_gitignore(self, tmp_path):
        """Test that _build_sparse_result excludes .gitignore from local components."""
        from cldpm.commands.get import _build_sparse_result

        # Set up mock temp directory structure
        project_path = "projects/test-project"
        shared_dir = "shared"

        # Create project directory
        project_dir = tmp_path / project_path
        project_dir.mkdir(parents=True)
        (project_dir / "project.json").write_text('{"name": "test-project"}')

        # Create .claude/skills directory with .gitignore and a skill
        local_skills_dir = project_dir / ".claude" / "skills"
        local_skills_dir.mkdir(parents=True)
        (local_skills_dir / ".gitignore").write_text("*")

        local_skill = local_skills_dir / "my-skill"
        local_skill.mkdir()
        (local_skill / "SKILL.md").write_text("# My Skill")

        project_config = {"name": "test-project"}
        dependencies = {"skills": [], "agents": [], "hooks": [], "rules": []}

        result = _build_sparse_result(
            tmp_path,
            "test-project",
            project_path,
            shared_dir,
            project_config,
            dependencies,
            "owner/repo",
            "https://github.com/owner/repo.git",
            None,
        )

        # Check that .gitignore is not included as a skill
        local_skills = result["local"]["skills"]
        assert len(local_skills) == 1
        assert local_skills[0]["name"] == "my-skill"
