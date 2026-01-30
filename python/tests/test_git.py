"""Tests for git utility functions."""

import os
from unittest import mock

import pytest

from cldpm.utils.git import get_github_token, parse_repo_url


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
