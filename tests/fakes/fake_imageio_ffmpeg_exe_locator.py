class FakeImageioFfmpegExeLocator:
    """Test double that returns a fixed ffmpeg path or ``None``."""

    def __init__(self, path: str | None) -> None:
        self._path = path

    def locate(self) -> str | None:
        """Return the configured path."""
        return self._path
