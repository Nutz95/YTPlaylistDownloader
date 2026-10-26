from dataclasses import dataclass


@dataclass(frozen=True)
class YtdlpFlatEntry:
    """One flat-playlist entry returned by a yt-dlp probe."""

    video_id: str
    title: str
    uploader: str
    duration_sec: int | None
    webpage_url: str
