"""File system utility functions."""

from pathlib import Path
from typing import Optional


def find_repo_root(start_path: Optional[Path] = None) -> Optional[Path]:
    """Find the root of a CPM mono repo by looking for cpm.json.

    Args:
        start_path: Starting directory to search from. Defaults to current directory.

    Returns:
        Path to the repo root, or None if not found.
    """
    if start_path is None:
        start_path = Path.cwd()

    current = start_path.resolve()

    while current != current.parent:
        if (current / "cpm.json").exists():
            return current
        current = current.parent

    # Check root directory
    if (current / "cpm.json").exists():
        return current

    return None


def ensure_dir(path: Path) -> Path:
    """Ensure a directory exists, creating it if necessary.

    Args:
        path: Path to the directory.

    Returns:
        The path to the directory.
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def is_symlink(path: Path) -> bool:
    """Check if a path is a symlink.

    Args:
        path: Path to check.

    Returns:
        True if the path is a symlink, False otherwise.
    """
    return path.is_symlink()


def remove_symlinks_in_dir(directory: Path) -> None:
    """Remove all symlinks in a directory.

    Args:
        directory: Directory to clean.
    """
    if not directory.exists():
        return

    for item in directory.iterdir():
        if item.is_symlink():
            item.unlink()


def copy_dir_contents(src: Path, dst: Path, follow_symlinks: bool = True) -> None:
    """Copy directory contents, optionally resolving symlinks.

    Args:
        src: Source directory.
        dst: Destination directory.
        follow_symlinks: If True, copy symlink targets. If False, copy symlinks as-is.
    """
    import shutil

    ensure_dir(dst)

    for item in src.iterdir():
        dest_path = dst / item.name

        if item.is_symlink() and follow_symlinks:
            # Resolve symlink and copy actual content
            resolved = item.resolve()
            if resolved.is_dir():
                shutil.copytree(resolved, dest_path)
            else:
                shutil.copy2(resolved, dest_path)
        elif item.is_dir():
            shutil.copytree(item, dest_path, symlinks=not follow_symlinks)
        else:
            shutil.copy2(item, dest_path)
