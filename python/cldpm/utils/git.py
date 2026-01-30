"""Git utility functions for remote repository operations."""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse


def get_github_token() -> Optional[str]:
    """Get GitHub token from environment variables.

    Checks GITHUB_TOKEN and GH_TOKEN in that order.

    Returns:
        The token if found, None otherwise.
    """
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")


def parse_repo_url(url: str) -> tuple[str, Optional[str], Optional[str]]:
    """Parse a repository URL to extract repo URL, optional path, and branch.

    Supports formats:
    - https://github.com/owner/repo
    - https://github.com/owner/repo/tree/branch
    - https://github.com/owner/repo/tree/branch/path/to/project
    - github.com/owner/repo
    - owner/repo (assumes GitHub)

    Args:
        url: The repository URL or shorthand.

    Returns:
        Tuple of (repo_url, subpath, branch).
    """
    original_url = url
    branch = None
    subpath = None

    # Handle shorthand owner/repo format
    if not url.startswith(("http://", "https://", "git@")) and "/" in url:
        if url.count("/") == 1:
            # Simple owner/repo format
            url = f"https://github.com/{url}"
        elif not url.startswith("github.com"):
            url = f"https://{url}"

    # Add https:// if missing
    if url.startswith("github.com"):
        url = f"https://{url}"

    # Parse the URL
    parsed = urlparse(url)
    path_parts = parsed.path.strip("/").split("/")

    if len(path_parts) >= 2:
        owner = path_parts[0]
        repo = path_parts[1]

        # Remove .git suffix if present
        if repo.endswith(".git"):
            repo = repo[:-4]

        # Check for /tree/branch/path pattern
        if len(path_parts) > 3 and path_parts[2] == "tree":
            branch = path_parts[3]
            if len(path_parts) > 4:
                subpath = "/".join(path_parts[4:])

        repo_url = f"https://{parsed.netloc}/{owner}/{repo}.git"
        return repo_url, subpath, branch

    raise ValueError(f"Invalid repository URL: {original_url}")


def clone_repo(
    repo_url: str,
    target_dir: Path,
    branch: Optional[str] = None,
    token: Optional[str] = None,
    sparse_paths: Optional[list[str]] = None,
) -> Path:
    """Clone a git repository.

    Args:
        repo_url: The repository URL.
        target_dir: Directory to clone into.
        branch: Optional branch to checkout.
        token: Optional GitHub token for authentication.
        sparse_paths: Optional list of paths for sparse checkout.

    Returns:
        Path to the cloned repository.

    Raises:
        subprocess.CalledProcessError: If git commands fail.
    """
    # Inject token into URL if provided
    if token and "github.com" in repo_url:
        repo_url = repo_url.replace(
            "https://github.com", f"https://{token}@github.com"
        )

    cmd = ["git", "clone", "--depth", "1"]

    if branch:
        cmd.extend(["--branch", branch])

    if sparse_paths:
        cmd.extend(["--filter=blob:none", "--sparse"])

    cmd.extend([repo_url, str(target_dir)])

    # Run clone with token hidden from output
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"

    subprocess.run(
        cmd,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )

    # Set up sparse checkout if needed
    if sparse_paths:
        subprocess.run(
            ["git", "sparse-checkout", "set"] + sparse_paths,
            cwd=target_dir,
            check=True,
            capture_output=True,
            text=True,
        )

    return target_dir


def clone_to_temp(
    repo_url: str,
    branch: Optional[str] = None,
    token: Optional[str] = None,
) -> Path:
    """Clone a repository to a temporary directory.

    Args:
        repo_url: The repository URL.
        branch: Optional branch to checkout.
        token: Optional GitHub token for authentication.

    Returns:
        Path to the temporary directory containing the clone.
    """
    temp_dir = Path(tempfile.mkdtemp(prefix="cldpm-"))
    clone_repo(repo_url, temp_dir, branch, token)
    return temp_dir


def cleanup_temp_dir(temp_dir: Path) -> None:
    """Clean up a temporary directory.

    Args:
        temp_dir: Path to the temporary directory.
    """
    if temp_dir.exists() and str(temp_dir).startswith(tempfile.gettempdir()):
        shutil.rmtree(temp_dir)
