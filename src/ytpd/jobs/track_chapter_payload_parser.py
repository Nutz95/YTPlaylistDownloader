from collections.abc import Mapping

from ytpd.domain.track_chapter_payload_fields import TrackChapterPayloadFields
from ytpd.jobs.invalid_job_error import InvalidJobError


class TrackChapterPayloadParser:
    """Validate optional chapter fields on a track JSON mapping."""

    def parse(self, item: Mapping[str, object]) -> TrackChapterPayloadFields:
        """Return typed chapter fields or raise ``InvalidJobError``."""
        chapter_start_sec = item.get("chapter_start_sec")
        chapter_end_sec = item.get("chapter_end_sec")
        parent_video_id = item.get("parent_video_id")
        chapter_index = item.get("chapter_index")
        if chapter_start_sec is not None and (
            isinstance(chapter_start_sec, bool)
            or not isinstance(chapter_start_sec, int | float)
        ):
            raise InvalidJobError("chapter_start_sec must be a number or null")
        if chapter_end_sec is not None and (
            isinstance(chapter_end_sec, bool)
            or not isinstance(chapter_end_sec, int | float)
        ):
            raise InvalidJobError("chapter_end_sec must be a number or null")
        if parent_video_id is not None and not isinstance(parent_video_id, str):
            raise InvalidJobError("parent_video_id must be a string or null")
        if chapter_index is not None and (
            isinstance(chapter_index, bool) or not isinstance(chapter_index, int)
        ):
            raise InvalidJobError("chapter_index must be an int or null")
        return TrackChapterPayloadFields(
            chapter_start_sec=(
                float(chapter_start_sec) if chapter_start_sec is not None else None
            ),
            chapter_end_sec=(
                float(chapter_end_sec) if chapter_end_sec is not None else None
            ),
            parent_video_id=parent_video_id if isinstance(parent_video_id, str) else None,
            chapter_index=chapter_index if isinstance(chapter_index, int) else None,
        )
