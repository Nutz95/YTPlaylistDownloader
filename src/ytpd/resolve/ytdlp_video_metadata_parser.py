import json
from collections.abc import Mapping

from ytpd.domain.ytdlp_chapter import YtdlpChapter
from ytpd.domain.ytdlp_video_metadata import YtdlpVideoMetadata
from ytpd.resolve.ytdlp_probe_error import YtdlpProbeError

_ChapterValue = str | int | float | bool | None


class YtdlpVideoMetadataParser:
    """Parse yt-dlp non-flat ``-J`` JSON into typed video metadata with chapters."""

    def parse(self, text: str) -> YtdlpVideoMetadata:
        """Parse a yt-dlp video JSON dump into ``YtdlpVideoMetadata``."""
        loaded = json.loads(text)
        if not isinstance(loaded, dict):
            raise YtdlpProbeError("yt-dlp JSON root must be an object")
        video_id = loaded.get("id")
        title = loaded.get("title")
        if not isinstance(video_id, str) or video_id.strip() == "":
            raise YtdlpProbeError("video missing id")
        if not isinstance(title, str) or title.strip() == "":
            raise YtdlpProbeError("video missing title")
        uploader_raw = loaded.get("uploader")
        if uploader_raw is None:
            uploader_raw = loaded.get("channel")
        uploader = uploader_raw if isinstance(uploader_raw, str) else ""
        duration_sec = self._parse_duration(loaded.get("duration"))
        webpage_raw = loaded.get("webpage_url")
        if isinstance(webpage_raw, str) and webpage_raw.strip() != "":
            webpage_url = webpage_raw
        else:
            webpage_url = f"https://www.youtube.com/watch?v={video_id}"
        chapters = self._parse_chapters(loaded.get("chapters"), duration_sec)
        return YtdlpVideoMetadata(
            video_id=video_id,
            title=title,
            uploader=uploader,
            duration_sec=duration_sec,
            webpage_url=webpage_url,
            chapters=chapters,
        )

    def _parse_duration(self, duration_raw: _ChapterValue) -> int | None:
        if duration_raw is None:
            return None
        if isinstance(duration_raw, bool) or not isinstance(duration_raw, int | float):
            raise YtdlpProbeError("video duration must be numeric")
        return int(duration_raw)

    def _parse_chapters(
        self,
        chapters_raw: list[Mapping[str, _ChapterValue]] | None,
        video_duration_sec: int | None,
    ) -> list[YtdlpChapter]:
        if chapters_raw is None:
            return []
        if not isinstance(chapters_raw, list):
            raise YtdlpProbeError("chapters must be a list")
        chapters: list[YtdlpChapter] = []
        for index, raw in enumerate(chapters_raw):
            if raw is None:
                continue
            if not isinstance(raw, dict):
                raise YtdlpProbeError(f"chapter {index} must be an object")
            chapters.append(self._parse_chapter(raw, index, video_duration_sec))
        return chapters

    def _parse_chapter(
        self,
        item: Mapping[str, _ChapterValue],
        index: int,
        video_duration_sec: int | None,
    ) -> YtdlpChapter:
        start_raw = item.get("start_time")
        if isinstance(start_raw, bool) or not isinstance(start_raw, int | float):
            raise YtdlpProbeError(f"chapter {index} missing start_time")
        end_raw = item.get("end_time")
        if end_raw is None and video_duration_sec is not None:
            end_sec = float(video_duration_sec)
        elif isinstance(end_raw, bool) or not isinstance(end_raw, int | float):
            raise YtdlpProbeError(f"chapter {index} missing end_time")
        else:
            end_sec = float(end_raw)
        title_raw = item.get("title")
        title = title_raw.strip() if isinstance(title_raw, str) else ""
        if title == "":
            title = f"Chapter {index + 1}"
        start_sec = float(start_raw)
        if end_sec <= start_sec:
            raise YtdlpProbeError(f"chapter {index} end_time must be after start_time")
        return YtdlpChapter(start_sec=start_sec, end_sec=end_sec, title=title)
