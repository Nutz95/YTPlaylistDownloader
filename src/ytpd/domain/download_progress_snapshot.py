from dataclasses import dataclass


@dataclass(frozen=True)
class DownloadProgressSnapshot:
    """Live download progress for one media file (possibly shared by chapters)."""

    media_key: str
    status: str
    percent: float | None
    downloaded_bytes: int | None
    total_bytes: int | None
    message: str
