from pathlib import Path


class OsPathUnlinker:
    """Delete regular files via ``Path.unlink``."""

    def try_unlink(self, path: Path) -> bool:
        """Return True when ``path`` is gone or was never a regular file."""
        if not path.is_file():
            return True
        try:
            path.unlink()
        except OSError:
            return not path.is_file()
        return not path.is_file()
