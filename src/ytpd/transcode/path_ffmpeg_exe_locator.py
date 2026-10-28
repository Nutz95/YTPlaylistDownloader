import shutil


class PathFfmpegExeLocator:
    """Locate ``ffmpeg`` via the process PATH (``shutil.which``)."""

    def locate(self) -> str | None:
        """Return the absolute ffmpeg path when found on PATH, else ``None``."""
        return shutil.which("ffmpeg")
