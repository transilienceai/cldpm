"""Tests for cpm link and unlink commands."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from cpm.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


def create_shared_component(comp_type: str, name: str, dependencies: dict = None) -> None:
    """Create a shared component for testing."""
    comp_path = Path(f"shared/{comp_type}/{name}")
    comp_path.mkdir(parents=True, exist_ok=True)

    singular = comp_type.rstrip("s")
    (comp_path / f"{singular.upper()}.md").write_text(f"# {name}\n")

    metadata = {"name": name}
    if dependencies:
        metadata["dependencies"] = dependencies

    (comp_path / f"{singular}.json").write_text(json.dumps(metadata, indent=2))


def test_link_single_dependency(runner, tmp_path):
    """Test linking a single dependency."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        create_shared_component("skills", "base-skill")
        create_shared_component("skills", "advanced-skill")

        result = runner.invoke(
            cli, ["link", "skill:base-skill", "--to", "skill:advanced-skill"]
        )

        assert result.exit_code == 0
        assert "Linked dependencies" in result.output
        assert "base-skill" in result.output

        # Verify metadata updated
        with open("shared/skills/advanced-skill/skill.json") as f:
            metadata = json.load(f)
        assert "base-skill" in metadata["dependencies"]["skills"]


def test_link_multiple_dependencies(runner, tmp_path):
    """Test linking multiple dependencies at once."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        create_shared_component("skills", "skill-a")
        create_shared_component("skills", "skill-b")
        create_shared_component("rules", "security")
        create_shared_component("agents", "auditor")

        result = runner.invoke(
            cli,
            ["link", "skill:skill-a,skill:skill-b,rule:security", "--to", "agent:auditor"],
        )

        assert result.exit_code == 0

        with open("shared/agents/auditor/agent.json") as f:
            metadata = json.load(f)
        assert "skill-a" in metadata["dependencies"]["skills"]
        assert "skill-b" in metadata["dependencies"]["skills"]
        assert "security" in metadata["dependencies"]["rules"]


def test_link_already_linked(runner, tmp_path):
    """Test linking a dependency that's already linked."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        create_shared_component("skills", "base-skill")
        create_shared_component("skills", "advanced-skill", {"skills": ["base-skill"]})

        result = runner.invoke(
            cli, ["link", "skill:base-skill", "--to", "skill:advanced-skill"]
        )

        assert result.exit_code == 0
        assert "Already linked" in result.output


def test_link_nonexistent_dependency(runner, tmp_path):
    """Test linking a dependency that doesn't exist."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        create_shared_component("skills", "advanced-skill")

        result = runner.invoke(
            cli, ["link", "skill:nonexistent", "--to", "skill:advanced-skill"]
        )

        assert result.exit_code == 1
        assert "not found" in result.output.lower()


def test_link_nonexistent_target(runner, tmp_path):
    """Test linking to a target that doesn't exist."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        create_shared_component("skills", "base-skill")

        result = runner.invoke(
            cli, ["link", "skill:base-skill", "--to", "skill:nonexistent"]
        )

        assert result.exit_code == 1
        assert "not found" in result.output.lower()


def test_link_cross_type_dependencies(runner, tmp_path):
    """Test linking dependencies of different types."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        create_shared_component("skills", "scan-skill")
        create_shared_component("hooks", "pre-commit")
        create_shared_component("rules", "security")
        create_shared_component("agents", "auditor")

        result = runner.invoke(
            cli,
            ["link", "skill:scan-skill,hook:pre-commit,rule:security", "--to", "agent:auditor"],
        )

        assert result.exit_code == 0

        with open("shared/agents/auditor/agent.json") as f:
            metadata = json.load(f)
        assert "scan-skill" in metadata["dependencies"]["skills"]
        assert "pre-commit" in metadata["dependencies"]["hooks"]
        assert "security" in metadata["dependencies"]["rules"]


def test_unlink_single_dependency(runner, tmp_path):
    """Test unlinking a single dependency."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        create_shared_component("skills", "base-skill")
        create_shared_component("skills", "advanced-skill", {"skills": ["base-skill"]})

        result = runner.invoke(
            cli, ["unlink", "skill:base-skill", "--from", "skill:advanced-skill"]
        )

        assert result.exit_code == 0
        assert "Unlinked dependencies" in result.output

        with open("shared/skills/advanced-skill/skill.json") as f:
            metadata = json.load(f)
        assert "dependencies" not in metadata or "skills" not in metadata.get("dependencies", {}) or "base-skill" not in metadata.get("dependencies", {}).get("skills", [])


def test_unlink_multiple_dependencies(runner, tmp_path):
    """Test unlinking multiple dependencies."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        create_shared_component("skills", "skill-a")
        create_shared_component("skills", "skill-b")
        create_shared_component("agents", "auditor", {"skills": ["skill-a", "skill-b"]})

        result = runner.invoke(
            cli, ["unlink", "skill:skill-a,skill:skill-b", "--from", "agent:auditor"]
        )

        assert result.exit_code == 0

        with open("shared/agents/auditor/agent.json") as f:
            metadata = json.load(f)
        skills = metadata.get("dependencies", {}).get("skills", [])
        assert "skill-a" not in skills
        assert "skill-b" not in skills


def test_unlink_not_linked(runner, tmp_path):
    """Test unlinking a dependency that isn't linked."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        create_shared_component("skills", "base-skill")
        create_shared_component("skills", "advanced-skill")

        result = runner.invoke(
            cli, ["unlink", "skill:base-skill", "--from", "skill:advanced-skill"]
        )

        assert result.exit_code == 0
        assert "Not linked" in result.output


def test_link_invalid_format(runner, tmp_path):
    """Test linking with invalid component format."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        create_shared_component("skills", "advanced-skill")

        result = runner.invoke(
            cli, ["link", "invalid-format", "--to", "skill:advanced-skill"]
        )

        assert result.exit_code == 1
        assert "Invalid component format" in result.output
