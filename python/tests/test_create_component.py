"""Tests for cldpm create component commands."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from cldpm.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


def test_create_skill(runner, tmp_path):
    """Test creating a shared skill."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])

        result = runner.invoke(cli, ["create", "skill", "code-review"])

        assert result.exit_code == 0
        assert "Created skill: code-review" in result.output

        # Verify files created
        skill_path = Path("shared/skills/code-review")
        assert skill_path.exists()
        assert (skill_path / "SKILL.md").exists()
        assert (skill_path / "skill.json").exists()

        # Verify metadata
        with open(skill_path / "skill.json") as f:
            metadata = json.load(f)
        assert metadata["name"] == "code-review"


def test_create_skill_with_description(runner, tmp_path):
    """Test creating a skill with description."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])

        result = runner.invoke(
            cli, ["create", "skill", "code-review", "-d", "Code review assistant"]
        )

        assert result.exit_code == 0

        with open("shared/skills/code-review/skill.json") as f:
            metadata = json.load(f)
        assert metadata["description"] == "Code review assistant"


def test_create_skill_with_dependencies(runner, tmp_path):
    """Test creating a skill with dependencies."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])

        result = runner.invoke(
            cli,
            [
                "create", "skill", "advanced-review",
                "--skills", "base-review,utils",
                "--rules", "security",
            ],
        )

        assert result.exit_code == 0
        assert "Dependencies:" in result.output

        with open("shared/skills/advanced-review/skill.json") as f:
            metadata = json.load(f)
        assert metadata["dependencies"]["skills"] == ["base-review", "utils"]
        assert metadata["dependencies"]["rules"] == ["security"]


def test_create_agent(runner, tmp_path):
    """Test creating a shared agent."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])

        result = runner.invoke(cli, ["create", "agent", "debugger"])

        assert result.exit_code == 0
        assert "Created agent: debugger" in result.output

        agent_path = Path("shared/agents/debugger")
        assert agent_path.exists()
        assert (agent_path / "AGENT.md").exists()
        assert (agent_path / "agent.json").exists()


def test_create_agent_with_all_dependencies(runner, tmp_path):
    """Test creating an agent with all dependency types."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])

        result = runner.invoke(
            cli,
            [
                "create", "agent", "full-audit",
                "-d", "Full audit agent",
                "-s", "scan,review",
                "-a", "helper",
                "-h", "pre-commit",
                "-r", "security,privacy",
            ],
        )

        assert result.exit_code == 0

        with open("shared/agents/full-audit/agent.json") as f:
            metadata = json.load(f)
        assert metadata["name"] == "full-audit"
        assert metadata["description"] == "Full audit agent"
        assert metadata["dependencies"]["skills"] == ["scan", "review"]
        assert metadata["dependencies"]["agents"] == ["helper"]
        assert metadata["dependencies"]["hooks"] == ["pre-commit"]
        assert metadata["dependencies"]["rules"] == ["security", "privacy"]


def test_create_hook(runner, tmp_path):
    """Test creating a shared hook."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])

        result = runner.invoke(cli, ["create", "hook", "pre-commit"])

        assert result.exit_code == 0
        assert "Created hook: pre-commit" in result.output

        hook_path = Path("shared/hooks/pre-commit")
        assert hook_path.exists()
        assert (hook_path / "HOOK.md").exists()
        assert (hook_path / "hook.json").exists()


def test_create_rule(runner, tmp_path):
    """Test creating a shared rule."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])

        result = runner.invoke(cli, ["create", "rule", "security"])

        assert result.exit_code == 0
        assert "Created rule: security" in result.output

        rule_path = Path("shared/rules/security")
        assert rule_path.exists()
        assert (rule_path / "RULE.md").exists()
        assert (rule_path / "rule.json").exists()


def test_create_rule_with_dependencies(runner, tmp_path):
    """Test creating a rule with rule dependencies."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])

        result = runner.invoke(
            cli,
            ["create", "rule", "full-compliance", "-r", "security,privacy,logging"],
        )

        assert result.exit_code == 0

        with open("shared/rules/full-compliance/rule.json") as f:
            metadata = json.load(f)
        assert metadata["dependencies"]["rules"] == ["security", "privacy", "logging"]


def test_create_component_already_exists(runner, tmp_path):
    """Test error when component already exists."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        runner.invoke(cli, ["create", "skill", "test-skill"])

        result = runner.invoke(cli, ["create", "skill", "test-skill"])

        assert result.exit_code == 1
        assert "already exists" in result.output.lower()


def test_create_component_not_in_repo(runner, tmp_path):
    """Test error when not in a CLDPM repo."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(cli, ["create", "skill", "test-skill"])

        assert result.exit_code == 1
        assert "Not in a CLDPM mono repo" in result.output
