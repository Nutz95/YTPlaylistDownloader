from dataclasses import dataclass

from ytpd.domain.ytdlp_chapter import YtdlpChapter


@dataclass(frozen=True)
class YtdlpVideoMetadata:
    """Full (non-flat) metadata for one YouTube video, including chapters."""

    video_id: str
    title: str
    uploader: str
    duration_sec: int | None
    webpage_url: str
    chapters: list[YtdlpChapter]
