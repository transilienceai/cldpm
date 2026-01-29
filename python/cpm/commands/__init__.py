"""CLI commands for CPM."""

from .init import init
from .create import create
from .add import add
from .remove import remove
from .get import get
from .clone import clone
from .sync import sync

__all__ = ["init", "create", "add", "remove", "get", "clone", "sync"]
