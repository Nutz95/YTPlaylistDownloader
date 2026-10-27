from dataclasses import dataclass


@dataclass(frozen=True)
class YtdlpChapter:
    """One chapter segment from a yt-dlp video metadata probe."""

    start_sec: float
    end_sec: float
    title: str
