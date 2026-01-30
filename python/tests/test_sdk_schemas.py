"""Tests for SDK schemas module."""

import json

import pytest
from pydantic import ValidationError

from cldpm.schemas import (
    CldpmConfig,
    ProjectConfig,
    ProjectDependencies,
    ComponentMetadata,
    ComponentDependencies,
)


class TestCldpmConfig:
    """Tests for CldpmConfig schema."""

    def test_create_with_all_fields(self):
        """Test creating config with all fields."""
        config = CldpmConfig(
            name="my-repo",
            version="2.0.0",
            projects_dir="apps",
            shared_dir="components",
        )

        assert config.name == "my-repo"
        assert config.version == "2.0.0"
        assert config.projects_dir == "apps"
        assert config.shared_dir == "components"

    def test_create_with_defaults(self):
        """Test creating config with default values."""
        config = CldpmConfig(name="my-repo")

        assert config.name == "my-repo"
        assert config.version == "1.0.0"
        assert config.projects_dir == "projects"
        assert config.shared_dir == "shared"

    def test_serialize_to_dict(self):
        """Test serializing to dictionary."""
        config = CldpmConfig(name="my-repo")
        data = config.model_dump(by_alias=True)

        assert data["name"] == "my-repo"
        assert data["projectsDir"] == "projects"
        assert data["sharedDir"] == "shared"

    def test_deserialize_from_dict(self):
        """Test deserializing from dictionary."""
        data = {
            "name": "test-repo",
            "version": "1.0.0",
            "projectsDir": "projects",
            "sharedDir": "shared",
        }

        config = CldpmConfig.model_validate(data)

        assert config.name == "test-repo"
        assert config.projects_dir == "projects"

    def test_name_required(self):
        """Test that name is required."""
        with pytest.raises(ValidationError):
            CldpmConfig()


class TestProjectDependencies:
    """Tests for ProjectDependencies schema."""

    def test_create_with_all_fields(self):
        """Test creating dependencies with all fields."""
        deps = ProjectDependencies(
            skills=["skill-a", "skill-b"],
            agents=["agent-x"],
            hooks=["hook-1"],
            rules=["rule-z"],
        )

        assert deps.skills == ["skill-a", "skill-b"]
        assert deps.agents == ["agent-x"]
        assert deps.hooks == ["hook-1"]
        assert deps.rules == ["rule-z"]

    def test_create_with_defaults(self):
        """Test creating dependencies with default empty lists."""
        deps = ProjectDependencies()

        assert deps.skills == []
        assert deps.agents == []
        assert deps.hooks == []
        assert deps.rules == []

    def test_serialize_to_dict(self):
        """Test serializing to dictionary."""
        deps = ProjectDependencies(skills=["skill-a"])
        data = deps.model_dump()

        assert data["skills"] == ["skill-a"]
        assert data["agents"] == []


class TestProjectConfig:
    """Tests for ProjectConfig schema."""

    def test_create_with_all_fields(self):
        """Test creating project config with all fields."""
        config = ProjectConfig(
            name="my-project",
            description="Test project",
            dependencies=ProjectDependencies(skills=["skill-a"]),
        )

        assert config.name == "my-project"
        assert config.description == "Test project"
        assert config.dependencies.skills == ["skill-a"]

    def test_create_with_defaults(self):
        """Test creating project config with defaults."""
        config = ProjectConfig(name="my-project")

        assert config.name == "my-project"
        assert config.description is None
        assert config.dependencies.skills == []

    def test_serialize_to_dict(self):
        """Test serializing to dictionary."""
        config = ProjectConfig(
            name="my-project",
            description="Test",
            dependencies=ProjectDependencies(skills=["skill-a"]),
        )
        data = config.model_dump(exclude_none=True)

        assert data["name"] == "my-project"
        assert data["description"] == "Test"
        assert data["dependencies"]["skills"] == ["skill-a"]

    def test_serialize_excludes_none(self):
        """Test that None values are excluded."""
        config = ProjectConfig(name="my-project")
        data = config.model_dump(exclude_none=True)

        assert "description" not in data

    def test_deserialize_from_dict(self):
        """Test deserializing from dictionary."""
        data = {
            "name": "test-project",
            "dependencies": {
                "skills": ["skill-a"],
                "agents": [],
                "hooks": [],
                "rules": [],
            },
        }

        config = ProjectConfig.model_validate(data)

        assert config.name == "test-project"
        assert config.dependencies.skills == ["skill-a"]


class TestComponentDependencies:
    """Tests for ComponentDependencies schema."""

    def test_create_with_all_fields(self):
        """Test creating component dependencies."""
        deps = ComponentDependencies(
            skills=["skill-a"],
            agents=["agent-b"],
            hooks=["hook-c"],
            rules=["rule-d"],
        )

        assert deps.skills == ["skill-a"]
        assert deps.agents == ["agent-b"]
        assert deps.hooks == ["hook-c"]
        assert deps.rules == ["rule-d"]

    def test_create_with_defaults(self):
        """Test creating with default empty lists."""
        deps = ComponentDependencies()

        assert deps.skills == []
        assert deps.agents == []
        assert deps.hooks == []
        assert deps.rules == []


class TestComponentMetadata:
    """Tests for ComponentMetadata schema."""

    def test_create_with_all_fields(self):
        """Test creating component metadata."""
        metadata = ComponentMetadata(
            name="my-component",
            description="Test component",
            dependencies=ComponentDependencies(skills=["skill-a"]),
        )

        assert metadata.name == "my-component"
        assert metadata.description == "Test component"
        assert metadata.dependencies.skills == ["skill-a"]

    def test_create_with_defaults(self):
        """Test creating with defaults."""
        metadata = ComponentMetadata(name="my-component")

        assert metadata.name == "my-component"
        assert metadata.description is None
        assert metadata.dependencies.skills == []

    def test_allows_extra_fields(self):
        """Test that extra fields are allowed."""
        data = {
            "name": "my-component",
            "version": "1.0.0",
            "author": "test",
        }

        metadata = ComponentMetadata.model_validate(data)

        assert metadata.name == "my-component"
        # Extra fields should be accessible
        assert hasattr(metadata, "version") or "version" in metadata.model_extra

    def test_serialize_to_dict(self):
        """Test serializing to dictionary."""
        metadata = ComponentMetadata(
            name="my-component",
            description="Test",
            dependencies=ComponentDependencies(skills=["skill-a"]),
        )
        data = metadata.model_dump()

        assert data["name"] == "my-component"
        assert data["description"] == "Test"
        assert data["dependencies"]["skills"] == ["skill-a"]

    def test_deserialize_from_dict(self):
        """Test deserializing from dictionary."""
        data = {
            "name": "test-component",
            "dependencies": {
                "skills": ["skill-a", "skill-b"],
            },
        }

        metadata = ComponentMetadata.model_validate(data)

        assert metadata.name == "test-component"
        assert metadata.dependencies.skills == ["skill-a", "skill-b"]
