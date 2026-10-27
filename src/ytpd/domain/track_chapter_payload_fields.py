from dataclasses import dataclass


@dataclass(frozen=True)
class TrackChapterPayloadFields:
    """Optional chapter slice fields parsed from a track JSON payload."""

    chapter_start_sec: float | None
    chapter_end_sec: float | None
    parent_video_id: str | None
    chapter_index: int | None
