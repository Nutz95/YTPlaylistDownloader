from dataclasses import dataclass


@dataclass(frozen=True)
class DownloadResult:
    """Outcome of downloading one track media file."""

    track_id: str
    success: bool
    output_path: str | None
    error_message: str | None
    bytes_downloaded: int
