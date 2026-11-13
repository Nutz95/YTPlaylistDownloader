from pathlib import Path
from typing import Protocol


class PathUnlinker(Protocol):
    """Remove a filesystem path when present."""

    def try_unlink(self, path: Path) -> bool:
        """Return True when ``path`` is gone or was never a regular file."""
