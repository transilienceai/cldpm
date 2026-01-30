"""Tests for SDK linker module."""

import json
import os
from pathlib import Path

import pytest

from cldpm.core.linker import (
    create_symlink,
    remove_project_links,
    update_component_gitignore,
    sync_project_links,
    add_component_link,
    get_local_components,
    get_shared_components,
)


@pytest.fixture
def setup_repo(tmp_path):
    """Set up a basic CLDPM repo structure."""
    # Create cldpm.json
    cldpm_config = {
        "name": "test-repo",
        "version": "1.0.0",
        "projectsDir": "projects",
        "sharedDir": "shared",
    }
    (tmp_path / "cldpm.json").write_text(json.dumps(cldpm_config))

    # Create directories
    (tmp_path / "projects").mkdir()
    for comp_type in ["skills", "agents", "hooks", "rules"]:
        (tmp_path / "shared" / comp_type).mkdir(parents=True)

    return tmp_path


def create_shared_component(repo_root: Path, comp_type: str, name: str):
    """Helper to create a shared component."""
    comp_path = repo_root / "shared" / comp_type / name
    comp_path.mkdir(parents=True, exist_ok=True)

    singular = comp_type.rstrip("s")
    (comp_path / f"{singular.upper()}.md").write_text(f"# {name}")
    (comp_path / f"{singular}.json").write_text(json.dumps({"name": name}))


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


class TestCreateSymlink:
    """Tests for create_symlink."""

    def test_create_valid_symlink(self, tmp_path):
        """Test creating a valid symlink."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "file.txt").write_text("content")

        target = tmp_path / "target" / "link"
        target.parent.mkdir(parents=True)

        result = create_symlink(source, target)

        assert result is True
        assert target.is_symlink()
        assert (target / "file.txt").exists()

    def test_create_symlink_replaces_existing(self, tmp_path):
        """Test that existing symlink is replaced."""
        source1 = tmp_path / "source1"
        source1.mkdir()

        source2 = tmp_path / "source2"
        source2.mkdir()
        (source2 / "new.txt").write_text("new")

        target = tmp_path / "link"
        target.symlink_to(source1)

        result = create_symlink(source2, target)

        assert result is True
        assert (target / "new.txt").exists()

    def test_create_symlink_fails_if_file_exists(self, tmp_path):
        """Test that symlink creation fails if non-symlink file exists."""
        source = tmp_path / "source"
        source.mkdir()

        target = tmp_path / "target"
        target.write_text("existing file")

        result = create_symlink(source, target)

        assert result is False
        assert not target.is_symlink()


class TestRemoveProjectLinks:
    """Tests for remove_project_links."""

    def test_remove_all_symlinks(self, setup_repo):
        """Test removing all symlinks from a project."""
        project_path = create_project(setup_repo, "my-project")
        create_shared_component(setup_repo, "skills", "skill-a")
        create_shared_component(setup_repo, "skills", "skill-b")

        # Create symlinks
        skills_dir = project_path / ".claude" / "skills"
        (skills_dir / "skill-a").symlink_to(setup_repo / "shared" / "skills" / "skill-a")
        (skills_dir / "skill-b").symlink_to(setup_repo / "shared" / "skills" / "skill-b")

        remove_project_links(project_path)

        assert not (skills_dir / "skill-a").exists()
        assert not (skills_dir / "skill-b").exists()

    def test_remove_preserves_local_components(self, setup_repo):
        """Test that local components are preserved."""
        project_path = create_project(setup_repo, "my-project")

        # Create local component
        local_skill = project_path / ".claude" / "skills" / "local-skill"
        local_skill.mkdir()
        (local_skill / "SKILL.md").write_text("# Local")

        # Create symlink
        create_shared_component(setup_repo, "skills", "shared-skill")
        (project_path / ".claude" / "skills" / "shared-skill").symlink_to(
            setup_repo / "shared" / "skills" / "shared-skill"
        )

        remove_project_links(project_path)

        assert local_skill.exists()
        assert not (project_path / ".claude" / "skills" / "shared-skill").exists()


class TestUpdateComponentGitignore:
    """Tests for update_component_gitignore."""

    def test_create_gitignore(self, tmp_path):
        """Test creating a .gitignore file."""
        comp_dir = tmp_path / "skills"
        comp_dir.mkdir()

        update_component_gitignore(comp_dir, ["skill-a", "skill-b"])

        gitignore = comp_dir / ".gitignore"
        assert gitignore.exists()
        content = gitignore.read_text()
        assert "skill-a" in content
        assert "skill-b" in content
        assert "CLDPM shared components" in content

    def test_remove_gitignore_when_empty(self, tmp_path):
        """Test removing .gitignore when no symlinks."""
        comp_dir = tmp_path / "skills"
        comp_dir.mkdir()

        # Create initial gitignore
        gitignore = comp_dir / ".gitignore"
        gitignore.write_text("# CLDPM shared components\nskill-a\n")

        update_component_gitignore(comp_dir, [])

        assert not gitignore.exists()

    def test_preserves_custom_gitignore(self, tmp_path):
        """Test that custom .gitignore content is preserved."""
        comp_dir = tmp_path / "skills"
        comp_dir.mkdir()

        # Create custom gitignore
        gitignore = comp_dir / ".gitignore"
        gitignore.write_text("# Custom content\n*.tmp\n")

        update_component_gitignore(comp_dir, [])

        # Should not be deleted since it doesn't start with CLDPM header
        assert gitignore.exists()
        assert "Custom content" in gitignore.read_text()


class TestSyncProjectLinks:
    """Tests for sync_project_links."""

    def test_sync_creates_symlinks(self, setup_repo):
        """Test that sync creates symlinks for dependencies."""
        create_shared_component(setup_repo, "skills", "skill-a")
        create_shared_component(setup_repo, "skills", "skill-b")
        project_path = create_project(setup_repo, "my-project", {
            "skills": ["skill-a", "skill-b"],
            "agents": [],
            "hooks": [],
            "rules": [],
        })

        result = sync_project_links(project_path, setup_repo)

        assert "skills/skill-a" in result["created"]
        assert "skills/skill-b" in result["created"]
        assert (project_path / ".claude" / "skills" / "skill-a").is_symlink()
        assert (project_path / ".claude" / "skills" / "skill-b").is_symlink()

    def test_sync_reports_missing(self, setup_repo):
        """Test that sync reports missing components."""
        project_path = create_project(setup_repo, "my-project", {
            "skills": ["nonexistent"],
            "agents": [],
            "hooks": [],
            "rules": [],
        })

        result = sync_project_links(project_path, setup_repo)

        assert "skills/nonexistent" in result["missing"]

    def test_sync_updates_gitignore(self, setup_repo):
        """Test that sync updates .gitignore."""
        create_shared_component(setup_repo, "skills", "skill-a")
        project_path = create_project(setup_repo, "my-project", {
            "skills": ["skill-a"],
            "agents": [],
            "hooks": [],
            "rules": [],
        })

        sync_project_links(project_path, setup_repo)

        gitignore = project_path / ".claude" / "skills" / ".gitignore"
        assert gitignore.exists()
        assert "skill-a" in gitignore.read_text()


class TestAddComponentLink:
    """Tests for add_component_link."""

    def test_add_single_link(self, setup_repo):
        """Test adding a single component link."""
        create_shared_component(setup_repo, "skills", "code-review")
        project_path = create_project(setup_repo, "my-project")

        result = add_component_link(project_path, "skills", "code-review", setup_repo)

        assert result is True
        assert (project_path / ".claude" / "skills" / "code-review").is_symlink()

    def test_add_updates_gitignore(self, setup_repo):
        """Test that adding a link updates .gitignore."""
        create_shared_component(setup_repo, "skills", "code-review")
        project_path = create_project(setup_repo, "my-project")

        add_component_link(project_path, "skills", "code-review", setup_repo)

        gitignore = project_path / ".claude" / "skills" / ".gitignore"
        assert "code-review" in gitignore.read_text()

    def test_add_nonexistent_fails(self, setup_repo):
        """Test that adding non-existent component fails."""
        project_path = create_project(setup_repo, "my-project")

        result = add_component_link(project_path, "skills", "nonexistent", setup_repo)

        assert result is False


class TestGetLocalComponents:
    """Tests for get_local_components."""

    def test_get_local_components(self, setup_repo):
        """Test getting local components."""
        project_path = create_project(setup_repo, "my-project")

        # Create local skills
        (project_path / ".claude" / "skills" / "local-a").mkdir()
        (project_path / ".claude" / "skills" / "local-b").mkdir()

        result = get_local_components(project_path)

        assert "local-a" in result["skills"]
        assert "local-b" in result["skills"]

    def test_ignores_symlinks(self, setup_repo):
        """Test that symlinks are not included."""
        project_path = create_project(setup_repo, "my-project")
        create_shared_component(setup_repo, "skills", "shared-skill")

        # Create symlink
        (project_path / ".claude" / "skills" / "shared-skill").symlink_to(
            setup_repo / "shared" / "skills" / "shared-skill"
        )

        # Create local
        (project_path / ".claude" / "skills" / "local-skill").mkdir()

        result = get_local_components(project_path)

        assert "local-skill" in result["skills"]
        assert "shared-skill" not in result["skills"]


class TestGetSharedComponents:
    """Tests for get_shared_components."""

    def test_get_shared_components(self, setup_repo):
        """Test getting shared (symlinked) components."""
        project_path = create_project(setup_repo, "my-project")
        create_shared_component(setup_repo, "skills", "shared-a")
        create_shared_component(setup_repo, "skills", "shared-b")

        # Create symlinks
        (project_path / ".claude" / "skills" / "shared-a").symlink_to(
            setup_repo / "shared" / "skills" / "shared-a"
        )
        (project_path / ".claude" / "skills" / "shared-b").symlink_to(
            setup_repo / "shared" / "skills" / "shared-b"
        )

        result = get_shared_components(project_path)

        assert "shared-a" in result["skills"]
        assert "shared-b" in result["skills"]

    def test_ignores_local_components(self, setup_repo):
        """Test that local components are not included."""
        project_path = create_project(setup_repo, "my-project")

        # Create local
        (project_path / ".claude" / "skills" / "local-skill").mkdir()

        result = get_shared_components(project_path)

        assert "local-skill" not in result["skills"]
