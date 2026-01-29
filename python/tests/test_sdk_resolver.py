"""Tests for SDK resolver module."""

import json
from pathlib import Path

import pytest

from cpm.core.resolver import (
    resolve_project,
    resolve_component,
    resolve_local_component,
    get_local_components_in_project,
    list_shared_components,
    resolve_component_dependencies,
    get_all_dependencies_for_component,
)


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
    for comp_type in ["skills", "agents", "hooks", "rules"]:
        (tmp_path / "shared" / comp_type).mkdir(parents=True)

    return tmp_path


def create_shared_component(repo_root: Path, comp_type: str, name: str, deps: dict = None):
    """Helper to create a shared component."""
    comp_path = repo_root / "shared" / comp_type / name
    comp_path.mkdir(parents=True, exist_ok=True)

    singular = comp_type.rstrip("s")
    (comp_path / f"{singular.upper()}.md").write_text(f"# {name}")

    metadata = {"name": name}
    if deps:
        metadata["dependencies"] = deps
    (comp_path / f"{singular}.json").write_text(json.dumps(metadata))


def create_project(repo_root: Path, name: str, deps: dict = None):
    """Helper to create a project."""
    project_path = repo_root / "projects" / name
    project_path.mkdir(parents=True)

    # Create .claude structure
    claude_dir = project_path / ".claude"
    for comp_type in ["skills", "agents", "hooks", "rules"]:
        (claude_dir / comp_type).mkdir(parents=True)

    config = {
        "name": name,
        "dependencies": deps or {"skills": [], "agents": [], "hooks": [], "rules": []},
    }
    (project_path / "project.json").write_text(json.dumps(config))

    return project_path


class TestResolveComponent:
    """Tests for resolve_component."""

    def test_resolve_existing_skill(self, setup_repo):
        """Test resolving an existing skill."""
        create_shared_component(setup_repo, "skills", "code-review")
        shared_dir = setup_repo / "shared"

        result = resolve_component("skills", "code-review", shared_dir)

        assert result is not None
        assert result["name"] == "code-review"
        assert result["type"] == "shared"
        assert "sourcePath" in result
        assert "files" in result

    def test_resolve_nonexistent_component(self, setup_repo):
        """Test resolving a non-existent component."""
        shared_dir = setup_repo / "shared"

        result = resolve_component("skills", "nonexistent", shared_dir)

        assert result is None


class TestResolveLocalComponent:
    """Tests for resolve_local_component."""

    def test_resolve_local_skill(self, setup_repo):
        """Test resolving a local skill."""
        project_path = create_project(setup_repo, "my-project")

        # Create local skill
        local_skill = project_path / ".claude" / "skills" / "local-skill"
        local_skill.mkdir()
        (local_skill / "SKILL.md").write_text("# Local Skill")

        result = resolve_local_component("skills", "local-skill", project_path)

        assert result is not None
        assert result["name"] == "local-skill"
        assert result["type"] == "local"

    def test_resolve_symlink_returns_none(self, setup_repo):
        """Test that symlinks are not resolved as local components."""
        project_path = create_project(setup_repo, "my-project")
        create_shared_component(setup_repo, "skills", "shared-skill")

        # Create symlink
        link_path = project_path / ".claude" / "skills" / "shared-skill"
        source = setup_repo / "shared" / "skills" / "shared-skill"
        link_path.symlink_to(source)

        result = resolve_local_component("skills", "shared-skill", project_path)

        assert result is None


class TestGetLocalComponentsInProject:
    """Tests for get_local_components_in_project."""

    def test_get_local_components(self, setup_repo):
        """Test getting all local components."""
        project_path = create_project(setup_repo, "my-project")

        # Create local components
        (project_path / ".claude" / "skills" / "local-skill-1").mkdir()
        (project_path / ".claude" / "skills" / "local-skill-2").mkdir()
        (project_path / ".claude" / "agents" / "local-agent").mkdir()

        result = get_local_components_in_project(project_path)

        assert len(result["skills"]) == 2
        assert len(result["agents"]) == 1
        assert len(result["hooks"]) == 0
        assert len(result["rules"]) == 0


class TestResolveProject:
    """Tests for resolve_project."""

    def test_resolve_by_name(self, setup_repo):
        """Test resolving project by name."""
        create_project(setup_repo, "my-project", {"skills": ["code-review"], "agents": [], "hooks": [], "rules": []})
        create_shared_component(setup_repo, "skills", "code-review")

        result = resolve_project("my-project", setup_repo)

        assert result["name"] == "my-project"
        assert "path" in result
        assert "config" in result
        assert "shared" in result
        assert "local" in result

    def test_resolve_by_path(self, setup_repo):
        """Test resolving project by path."""
        create_project(setup_repo, "my-project")

        result = resolve_project("projects/my-project", setup_repo)

        assert result["name"] == "my-project"

    def test_resolve_with_shared_dependencies(self, setup_repo):
        """Test resolving project with shared dependencies."""
        create_shared_component(setup_repo, "skills", "skill-a")
        create_shared_component(setup_repo, "skills", "skill-b")
        create_project(setup_repo, "my-project", {
            "skills": ["skill-a", "skill-b"],
            "agents": [],
            "hooks": [],
            "rules": [],
        })

        result = resolve_project("my-project", setup_repo)

        assert len(result["shared"]["skills"]) == 2
        names = [s["name"] for s in result["shared"]["skills"]]
        assert "skill-a" in names
        assert "skill-b" in names

    def test_resolve_nonexistent_project(self, setup_repo):
        """Test resolving non-existent project raises error."""
        with pytest.raises(FileNotFoundError):
            resolve_project("nonexistent", setup_repo)


class TestListSharedComponents:
    """Tests for list_shared_components."""

    def test_list_all_components(self, setup_repo):
        """Test listing all shared components."""
        create_shared_component(setup_repo, "skills", "skill-a")
        create_shared_component(setup_repo, "skills", "skill-b")
        create_shared_component(setup_repo, "agents", "agent-x")

        result = list_shared_components(setup_repo)

        assert "skill-a" in result["skills"]
        assert "skill-b" in result["skills"]
        assert "agent-x" in result["agents"]
        assert result["hooks"] == []
        assert result["rules"] == []


class TestResolveComponentDependencies:
    """Tests for resolve_component_dependencies."""

    def test_resolve_simple_dependencies(self, setup_repo):
        """Test resolving simple dependencies."""
        create_shared_component(setup_repo, "skills", "base-skill")
        create_shared_component(setup_repo, "skills", "main-skill", {
            "skills": ["base-skill"]
        })

        result = resolve_component_dependencies("skills", "main-skill", setup_repo)

        assert ("skills", "base-skill") in result

    def test_resolve_transitive_dependencies(self, setup_repo):
        """Test resolving transitive dependencies."""
        create_shared_component(setup_repo, "skills", "level-1")
        create_shared_component(setup_repo, "skills", "level-2", {"skills": ["level-1"]})
        create_shared_component(setup_repo, "skills", "level-3", {"skills": ["level-2"]})

        result = resolve_component_dependencies("skills", "level-3", setup_repo)

        assert ("skills", "level-2") in result
        assert ("skills", "level-1") in result

    def test_resolve_cross_type_dependencies(self, setup_repo):
        """Test resolving cross-type dependencies."""
        create_shared_component(setup_repo, "skills", "helper-skill")
        create_shared_component(setup_repo, "rules", "security-rule")
        create_shared_component(setup_repo, "agents", "main-agent", {
            "skills": ["helper-skill"],
            "rules": ["security-rule"],
        })

        result = resolve_component_dependencies("agents", "main-agent", setup_repo)

        assert ("skills", "helper-skill") in result
        assert ("rules", "security-rule") in result

    def test_resolve_no_dependencies(self, setup_repo):
        """Test resolving component with no dependencies."""
        create_shared_component(setup_repo, "skills", "standalone")

        result = resolve_component_dependencies("skills", "standalone", setup_repo)

        assert result == []


class TestGetAllDependenciesForComponent:
    """Tests for get_all_dependencies_for_component."""

    def test_get_dependencies_organized_by_type(self, setup_repo):
        """Test getting dependencies organized by type."""
        create_shared_component(setup_repo, "skills", "skill-a")
        create_shared_component(setup_repo, "skills", "skill-b")
        create_shared_component(setup_repo, "hooks", "hook-x")
        create_shared_component(setup_repo, "agents", "main-agent", {
            "skills": ["skill-a", "skill-b"],
            "hooks": ["hook-x"],
        })

        result = get_all_dependencies_for_component("agents", "main-agent", setup_repo)

        assert "skill-a" in result["skills"]
        assert "skill-b" in result["skills"]
        assert "hook-x" in result["hooks"]
        assert result["agents"] == []
        assert result["rules"] == []

    def test_get_dependencies_no_duplicates(self, setup_repo):
        """Test that duplicate dependencies are not returned."""
        create_shared_component(setup_repo, "skills", "common")
        create_shared_component(setup_repo, "skills", "skill-a", {"skills": ["common"]})
        create_shared_component(setup_repo, "skills", "skill-b", {"skills": ["common"]})
        create_shared_component(setup_repo, "agents", "main-agent", {
            "skills": ["skill-a", "skill-b"],
        })

        result = get_all_dependencies_for_component("agents", "main-agent", setup_repo)

        # "common" should appear only once
        assert result["skills"].count("common") == 1
