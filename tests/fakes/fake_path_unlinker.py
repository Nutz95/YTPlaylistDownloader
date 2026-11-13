from pathlib import Path


class FakePathUnlinker:
    """Path unlinker that can refuse specific paths for lock simulations."""

    def __init__(self, refuse: list[Path] | None = None) -> None:
        self._refuse = {path.resolve() for path in (refuse or [])}

    def try_unlink(self, path: Path) -> bool:
        """Delete ``path`` unless it was listed in ``refuse`` at construction."""
        if path.resolve() in self._refuse:
            return False
        if not path.is_file():
            return True
        path.unlink()
        return not path.is_file()
