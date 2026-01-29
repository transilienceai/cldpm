"""Tests for SDK config module."""

import json
from pathlib import Path

import pytest

from cpm.core.config import (
    load_cpm_config,
    save_cpm_config,
    load_project_config,
    save_project_config,
    get_project_path,
    list_projects,
    load_component_metadata,
)
from cpm.schemas import CpmConfig, ProjectConfig, ProjectDependencies


@pytest.fixture
def setup_repo(tmp_path):
    """Set up a basic CPM repo structure."""
    # Create cpm.json
    cpm_config = {
        "name": "test-repo",
        "version": "1.0.0",
        "projectsDir": "projects",
        "sharedDir": "shared",
    }
    (tmp_path / "cpm.json").write_text(json.dumps(cpm_config))

    # Create directories
    (tmp_path / "projects").mkdir()
    (tmp_path / "shared" / "skills").mkdir(parents=True)
    (tmp_path / "shared" / "agents").mkdir(parents=True)

    return tmp_path


class TestLoadCpmConfig:
    """Tests for load_cpm_config."""

    def test_load_valid_config(self, setup_repo):
        """Test loading a valid cpm.json."""
        config = load_cpm_config(setup_repo)

        assert config.name == "test-repo"
        assert config.version == "1.0.0"
        assert config.projects_dir == "projects"
        assert config.shared_dir == "shared"

    def test_load_missing_config(self, tmp_path):
        """Test loading from directory without cpm.json."""
        with pytest.raises(FileNotFoundError):
            load_cpm_config(tmp_path)

    def test_load_config_with_defaults(self, tmp_path):
        """Test loading config with minimal fields uses defaults."""
        config = {"name": "minimal-repo"}
        (tmp_path / "cpm.json").write_text(json.dumps(config))

        loaded = load_cpm_config(tmp_path)

        assert loaded.name == "minimal-repo"
        assert loaded.version == "1.0.0"  # default
        assert loaded.projects_dir == "projects"  # default
        assert loaded.shared_dir == "shared"  # default


class TestSaveCpmConfig:
    """Tests for save_cpm_config."""

    def test_save_config(self, tmp_path):
        """Test saving a CPM config."""
        config = CpmConfig(
            name="new-repo",
            version="2.0.0",
            projects_dir="apps",
            shared_dir="components",
        )

        save_cpm_config(config, tmp_path)

        # Verify saved
        with open(tmp_path / "cpm.json") as f:
            saved = json.load(f)

        assert saved["name"] == "new-repo"
        assert saved["version"] == "2.0.0"
        assert saved["projectsDir"] == "apps"
        assert saved["sharedDir"] == "components"


class TestLoadProjectConfig:
    """Tests for load_project_config."""

    def test_load_valid_project(self, setup_repo):
        """Test loading a valid project.json."""
        project_path = setup_repo / "projects" / "my-project"
        project_path.mkdir()

        project_config = {
            "name": "my-project",
            "description": "Test project",
            "dependencies": {
                "skills": ["skill-a", "skill-b"],
                "agents": [],
                "hooks": [],
                "rules": [],
            },
        }
        (project_path / "project.json").write_text(json.dumps(project_config))

        loaded = load_project_config(project_path)

        assert loaded.name == "my-project"
        assert loaded.description == "Test project"
        assert loaded.dependencies.skills == ["skill-a", "skill-b"]

    def test_load_missing_project(self, tmp_path):
        """Test loading from directory without project.json."""
        with pytest.raises(FileNotFoundError):
            load_project_config(tmp_path)


class TestSaveProjectConfig:
    """Tests for save_project_config."""

    def test_save_project(self, tmp_path):
        """Test saving a project config."""
        config = ProjectConfig(
            name="test-project",
            description="A test project",
            dependencies=ProjectDependencies(
                skills=["code-review"],
                agents=["debugger"],
            ),
        )

        save_project_config(config, tmp_path)

        with open(tmp_path / "project.json") as f:
            saved = json.load(f)

        assert saved["name"] == "test-project"
        assert saved["description"] == "A test project"
        assert saved["dependencies"]["skills"] == ["code-review"]
        assert saved["dependencies"]["agents"] == ["debugger"]


class TestGetProjectPath:
    """Tests for get_project_path."""

    def test_get_existing_project(self, setup_repo):
        """Test getting path for existing project."""
        project_path = setup_repo / "projects" / "my-project"
        project_path.mkdir()
        (project_path / "project.json").write_text('{"name": "my-project"}')

        result = get_project_path("my-project", setup_repo)

        assert result == project_path

    def test_get_nonexistent_project(self, setup_repo):
        """Test getting path for non-existent project."""
        result = get_project_path("nonexistent", setup_repo)

        assert result is None


class TestListProjects:
    """Tests for list_projects."""

    def test_list_multiple_projects(self, setup_repo):
        """Test listing multiple projects."""
        for name in ["project-a", "project-b", "project-c"]:
            project_path = setup_repo / "projects" / name
            project_path.mkdir()
            (project_path / "project.json").write_text(f'{{"name": "{name}"}}')

        projects = list_projects(setup_repo)

        assert len(projects) == 3
        names = [p.name for p in projects]
        assert "project-a" in names
        assert "project-b" in names
        assert "project-c" in names

    def test_list_empty(self, setup_repo):
        """Test listing when no projects exist."""
        projects = list_projects(setup_repo)

        assert projects == []

    def test_list_ignores_non_projects(self, setup_repo):
        """Test that directories without project.json are ignored."""
        (setup_repo / "projects" / "not-a-project").mkdir()
        (setup_repo / "projects" / "real-project").mkdir()
        (setup_repo / "projects" / "real-project" / "project.json").write_text(
            '{"name": "real-project"}'
        )

        projects = list_projects(setup_repo)

        assert len(projects) == 1
        assert projects[0].name == "real-project"


class TestLoadComponentMetadata:
    """Tests for load_component_metadata."""

    def test_load_skill_metadata(self, setup_repo):
        """Test loading skill metadata."""
        skill_path = setup_repo / "shared" / "skills" / "code-review"
        skill_path.mkdir()
        metadata = {
            "name": "code-review",
            "description": "Code review skill",
            "dependencies": {"skills": ["base-utils"]},
        }
        (skill_path / "skill.json").write_text(json.dumps(metadata))

        loaded = load_component_metadata("skills", "code-review", setup_repo)

        assert loaded is not None
        assert loaded.name == "code-review"
        assert loaded.description == "Code review skill"
        assert loaded.dependencies.skills == ["base-utils"]

    def test_load_agent_metadata(self, setup_repo):
        """Test loading agent metadata."""
        agent_path = setup_repo / "shared" / "agents" / "debugger"
        agent_path.mkdir()
        metadata = {
            "name": "debugger",
            "dependencies": {"skills": ["analysis", "logging"]},
        }
        (agent_path / "agent.json").write_text(json.dumps(metadata))

        loaded = load_component_metadata("agents", "debugger", setup_repo)

        assert loaded is not None
        assert loaded.name == "debugger"
        assert loaded.dependencies.skills == ["analysis", "logging"]

    def test_load_nonexistent_component(self, setup_repo):
        """Test loading non-existent component returns None."""
        loaded = load_component_metadata("skills", "nonexistent", setup_repo)

        assert loaded is None

    def test_load_component_without_metadata_file(self, setup_repo):
        """Test loading component without metadata file returns minimal metadata."""
        skill_path = setup_repo / "shared" / "skills" / "simple-skill"
        skill_path.mkdir()
        (skill_path / "SKILL.md").write_text("# Simple Skill")

        loaded = load_component_metadata("skills", "simple-skill", setup_repo)

        assert loaded is not None
        assert loaded.name == "simple-skill"
        assert loaded.dependencies.skills == []
