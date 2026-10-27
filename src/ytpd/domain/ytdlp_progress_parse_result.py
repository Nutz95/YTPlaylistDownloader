from dataclasses import dataclass


@dataclass(frozen=True)
class YtdlpProgressParseResult:
    """Fields extracted from one yt-dlp download progress line."""

    percent: float
    downloaded_bytes: int | None
    total_bytes: int | None
    message: str
