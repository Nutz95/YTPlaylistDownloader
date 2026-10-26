from dataclasses import dataclass


@dataclass(frozen=True)
class YtdlpDownloadAttempt:
    """Raw outcome of one yt-dlp download subprocess invocation."""

    success: bool
    detail: str
