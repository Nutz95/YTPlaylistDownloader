from pathlib import Path
from unittest.mock import MagicMock


class RecordingFfmpegRunner:
    """Capture ffmpeg argv and write a stub temporary output file."""

    def __init__(self) -> None:
        self.last_argv: list[str] = []

    def run(self, argv: list[str], timeout_sec: float) -> MagicMock:
        """Record argv, create the temp output path, and return success."""
        del timeout_sec
        self.last_argv = list(argv)
        temporary = Path(argv[-1])
        temporary.write_bytes(b"mp3")
        completed = MagicMock()
        completed.returncode = 0
        completed.stderr = ""
        completed.stdout = ""
        return completed
