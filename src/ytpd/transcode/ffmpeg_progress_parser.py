import re

_OUT_TIME_MS = re.compile(r"^out_time_ms=(\d+)\s*$")
_OUT_TIME = re.compile(r"^out_time=(\d+):(\d+):(\d+(?:\.\d+)?)\s*$")
_PROGRESS_END = re.compile(r"^progress=end\s*$")


class FfmpegProgressParser:
    """Parse ffmpeg ``-progress`` key/value lines into elapsed seconds."""

    def elapsed_sec(self, line: str) -> float | None:
        """Return elapsed media time in seconds from one progress line."""
        stripped = line.strip()
        ms_match = _OUT_TIME_MS.match(stripped)
        if ms_match is not None:
            return int(ms_match.group(1)) / 1_000_000.0
        time_match = _OUT_TIME.match(stripped)
        if time_match is not None:
            hours = int(time_match.group(1))
            minutes = int(time_match.group(2))
            seconds = float(time_match.group(3))
            return hours * 3600.0 + minutes * 60.0 + seconds
        return None

    def is_end(self, line: str) -> bool:
        """True when ffmpeg reports ``progress=end``."""
        return _PROGRESS_END.match(line.strip()) is not None
