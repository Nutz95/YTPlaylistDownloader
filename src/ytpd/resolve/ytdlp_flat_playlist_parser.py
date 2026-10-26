import json
from collections.abc import Mapping

from ytpd.domain.ytdlp_flat_entry import YtdlpFlatEntry
from ytpd.resolve.ytdlp_probe_error import YtdlpProbeError


class YtdlpFlatPlaylistParser:
    """Parse yt-dlp ``--flat-playlist -J`` JSON into typed flat entries."""

    def parse(self, text: str) -> list[YtdlpFlatEntry]:
        """Parse a yt-dlp JSON dump into flat entries."""
        loaded = json.loads(text)
        if not isinstance(loaded, dict):
            raise YtdlpProbeError("yt-dlp JSON root must be an object")
        if "entries" in loaded:
            entries_raw = loaded.get("entries")
            if entries_raw is None:
                return []
            if not isinstance(entries_raw, list):
                raise YtdlpProbeError("yt-dlp entries must be a list")
            tracks: list[YtdlpFlatEntry] = []
            for index, raw in enumerate(entries_raw):
                if raw is None:
                    continue
                if not isinstance(raw, dict):
                    raise YtdlpProbeError(f"entry {index} must be an object")
                tracks.append(self._parse_entry(raw, index))
            return tracks
        return [self._parse_entry(loaded, 0)]

    def _parse_entry(
        self,
        item: Mapping[str, str | int | float | bool | None],
        index: int,
    ) -> YtdlpFlatEntry:
        video_id = item.get("id")
        title = item.get("title")
        if not isinstance(video_id, str) or video_id.strip() == "":
            raise YtdlpProbeError(f"entry {index} missing id")
        if not isinstance(title, str) or title.strip() == "":
            raise YtdlpProbeError(f"entry {index} missing title")
        uploader_raw = item.get("uploader")
        if uploader_raw is None:
            uploader_raw = item.get("channel")
        uploader = uploader_raw if isinstance(uploader_raw, str) else ""
        duration_raw = item.get("duration")
        duration_sec: int | None
        if duration_raw is None:
            duration_sec = None
        elif isinstance(duration_raw, bool) or not isinstance(duration_raw, int | float):
            raise YtdlpProbeError(f"entry {index} duration must be numeric")
        else:
            duration_sec = int(duration_raw)
        webpage_raw = item.get("webpage_url")
        if isinstance(webpage_raw, str) and webpage_raw.strip() != "":
            webpage_url = webpage_raw
        else:
            webpage_url = f"https://www.youtube.com/watch?v={video_id}"
        return YtdlpFlatEntry(
            video_id=video_id,
            title=title,
            uploader=uploader,
            duration_sec=duration_sec,
            webpage_url=webpage_url,
        )
