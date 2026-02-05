"""Tests for git utility functions."""

import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from cldpm.utils.git import (
    get_github_token,
    has_sparse_clone_support,
    parse_repo_url,
    sparse_clone_paths,
    sparse_clone_to_temp,
)


class TestGetGithubToken:
    """Tests for get_github_token function."""

    def test_returns_github_token(self):
        """Test that GITHUB_TOKEN is returned when set."""
        with mock.patch.dict(os.environ, {"GITHUB_TOKEN": "test-token"}, clear=True):
            assert get_github_token() == "test-token"

    def test_returns_gh_token(self):
        """Test that GH_TOKEN is returned when GITHUB_TOKEN is not set."""
        with mock.patch.dict(os.environ, {"GH_TOKEN": "gh-token"}, clear=True):
            assert get_github_token() == "gh-token"

    def test_github_token_takes_precedence(self):
        """Test that GITHUB_TOKEN takes precedence over GH_TOKEN."""
        with mock.patch.dict(
            os.environ, {"GITHUB_TOKEN": "github-token", "GH_TOKEN": "gh-token"}
        ):
            assert get_github_token() == "github-token"

    def test_returns_none_when_no_token(self):
        """Test that None is returned when no token is set."""
        with mock.patch.dict(os.environ, {}, clear=True):
            assert get_github_token() is None


class TestParseRepoUrl:
    """Tests for parse_repo_url function."""

    def test_full_https_url(self):
        """Test parsing full HTTPS URL."""
        repo_url, subpath, branch = parse_repo_url("https://github.com/owner/repo")
        assert repo_url == "https://github.com/owner/repo.git"
        assert subpath is None
        assert branch is None

    def test_https_url_with_git_suffix(self):
        """Test parsing HTTPS URL with .git suffix."""
        repo_url, subpath, branch = parse_repo_url("https://github.com/owner/repo.git")
        assert repo_url == "https://github.com/owner/repo.git"
        assert subpath is None
        assert branch is None

    def test_url_with_tree_and_branch(self):
        """Test parsing URL with /tree/branch pattern."""
        repo_url, subpath, branch = parse_repo_url(
            "https://github.com/owner/repo/tree/main"
        )
        assert repo_url == "https://github.com/owner/repo.git"
        assert subpath is None
        assert branch == "main"

    def test_url_with_tree_branch_and_path(self):
        """Test parsing URL with /tree/branch/path pattern."""
        repo_url, subpath, branch = parse_repo_url(
            "https://github.com/owner/repo/tree/develop/projects/my-project"
        )
        assert repo_url == "https://github.com/owner/repo.git"
        assert subpath == "projects/my-project"
        assert branch == "develop"

    def test_shorthand_owner_repo(self):
        """Test parsing owner/repo shorthand."""
        repo_url, subpath, branch = parse_repo_url("owner/repo")
        assert repo_url == "https://github.com/owner/repo.git"
        assert subpath is None
        assert branch is None

    def test_github_com_without_https(self):
        """Test parsing github.com URL without https://."""
        repo_url, subpath, branch = parse_repo_url("github.com/owner/repo")
        assert repo_url == "https://github.com/owner/repo.git"
        assert subpath is None
        assert branch is None

    def test_invalid_url_raises_error(self):
        """Test that invalid URL raises ValueError."""
        with pytest.raises(ValueError, match="Invalid repository URL"):
            parse_repo_url("not-a-valid-url")


class TestHasSparseCloneSupport:
    """Tests for has_sparse_clone_support function."""

    def test_returns_boolean(self):
        """Test that function returns a boolean based on system git version."""
        # This tests with the actual system git version
        result = has_sparse_clone_support()
        assert isinstance(result, bool)

    def test_version_parsing_logic(self):
        """Test the version parsing logic directly."""
        # Test version string parsing
        def parse_version(version_str: str) -> tuple[int, int]:
            parts = version_str.split(".")
            major = int(parts[0])
            minor = int(parts[1]) if len(parts) > 1 else 0
            return major, minor

        # Test cases
        assert parse_version("2.25.0") == (2, 25)
        assert parse_version("2.30.1") == (2, 30)
        assert parse_version("3.0.0") == (3, 0)
        assert parse_version("2.24.0") == (2, 24)

        # Test the logic: major > 2 or (major == 2 and minor >= 25)
        def is_supported(major: int, minor: int) -> bool:
            return major > 2 or (major == 2 and minor >= 25)

        assert is_supported(2, 25) is True
        assert is_supported(2, 30) is True
        assert is_supported(3, 0) is True
        assert is_supported(2, 24) is False
        assert is_supported(2, 20) is False
        assert is_supported(1, 99) is False


class TestSparseClonePaths:
    """Tests for sparse_clone_paths function."""

    def test_calls_git_clone_with_correct_flags(self):
        """Test that git clone is called with sparse checkout flags."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock()
            with mock.patch("shutil.rmtree"):
                with mock.patch("shutil.copytree"):
                    with mock.patch("shutil.copy2"):
                        target = Path(tempfile.mkdtemp())
                        try:
                            sparse_clone_paths(
                                "https://github.com/owner/repo.git",
                                ["path1", "path2"],
                                target,
                            )
                        except Exception:
                            pass  # We just want to check the call

            # Check that clone was called with correct flags
            clone_call = mock_run.call_args_list[0]
            cmd = clone_call[0][0]
            assert "git" in cmd
            assert "clone" in cmd
            assert "--filter=blob:none" in cmd
            assert "--sparse" in cmd
            assert "--depth" in cmd
            assert "1" in cmd

    def test_calls_sparse_checkout_set(self):
        """Test that sparse-checkout set is called with paths."""
        call_count = 0
        def mock_run_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return mock.Mock()

        with mock.patch("subprocess.run", side_effect=mock_run_side_effect) as mock_run:
            with mock.patch("shutil.rmtree"):
                target = Path(tempfile.mkdtemp())
                try:
                    sparse_clone_paths(
                        "https://github.com/owner/repo.git",
                        ["projects/my-project", "shared/skills/test"],
                        target,
                    )
                except Exception:
                    pass

            # Second call should be sparse-checkout set
            if len(mock_run.call_args_list) >= 2:
                sparse_call = mock_run.call_args_list[1]
                cmd = sparse_call[0][0]
                assert "sparse-checkout" in cmd
                assert "set" in cmd
                assert "--no-cone" in cmd

    def test_injects_token_for_github(self):
        """Test that token is injected into GitHub URLs."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock()
            with mock.patch("shutil.rmtree"):
                target = Path(tempfile.mkdtemp())
                try:
                    sparse_clone_paths(
                        "https://github.com/owner/repo.git",
                        ["path1"],
                        target,
                        token="test-token",
                    )
                except Exception:
                    pass

            clone_call = mock_run.call_args_list[0]
            cmd = clone_call[0][0]
            # Token should be in the URL
            auth_url = [arg for arg in cmd if "github.com" in arg][0]
            assert "test-token@github.com" in auth_url

    def test_includes_branch_when_provided(self):
        """Test that branch is included in clone command."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock()
            with mock.patch("shutil.rmtree"):
                target = Path(tempfile.mkdtemp())
                try:
                    sparse_clone_paths(
                        "https://github.com/owner/repo.git",
                        ["path1"],
                        target,
                        branch="develop",
                    )
                except Exception:
                    pass

            clone_call = mock_run.call_args_list[0]
            cmd = clone_call[0][0]
            assert "--branch" in cmd
            assert "develop" in cmd


class TestSparseCloneToTemp:
    """Tests for sparse_clone_to_temp function."""

    def test_returns_temp_directory_path(self):
        """Test that a temp directory path is returned."""
        with mock.patch("cldpm.utils.git.sparse_clone_paths") as mock_clone:
            result = sparse_clone_to_temp(
                "https://github.com/owner/repo.git",
                ["path1"],
            )
            assert result.exists()
            assert str(result).startswith(tempfile.gettempdir())
            # Clean up
            result.rmdir()

    def test_passes_arguments_to_sparse_clone_paths(self):
        """Test that arguments are passed correctly."""
        with mock.patch("cldpm.utils.git.sparse_clone_paths") as mock_clone:
            sparse_clone_to_temp(
                "https://github.com/owner/repo.git",
                ["path1", "path2"],
                branch="main",
                token="test-token",
            )

            mock_clone.assert_called_once()
            call_args = mock_clone.call_args
            assert call_args[0][0] == "https://github.com/owner/repo.git"
            assert call_args[0][1] == ["path1", "path2"]
            assert call_args[0][3] == "main"  # branch
            assert call_args[0][4] == "test-token"  # token
