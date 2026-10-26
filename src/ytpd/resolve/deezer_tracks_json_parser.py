import json
from collections.abc import Mapping

from ytpd.domain.deezer_track_entry import DeezerTrackEntry
from ytpd.resolve.deezer_api_error import DeezerApiError
from ytpd.resolve.deezer_tracks_page import DeezerTracksPage


class DeezerTracksJsonParser:
    """Parse one Deezer tracks JSON page into typed entries."""

    def parse_text(self, text: str) -> DeezerTracksPage:
        """Parse a Deezer tracks JSON body into a page."""
        try:
            loaded = json.loads(text)
        except json.JSONDecodeError as error:
            raise DeezerApiError(f"deezer tracks JSON is invalid: {error}") from error
        if not isinstance(loaded, dict):
            raise DeezerApiError("deezer tracks payload must be an object")
        data_raw = loaded.get("data")
        if not isinstance(data_raw, list):
            raise DeezerApiError("deezer tracks payload missing data list")
        tracks: list[DeezerTrackEntry] = []
        for index, item in enumerate(data_raw):
            if not isinstance(item, dict):
                raise DeezerApiError(f"deezer track {index} must be an object")
            tracks.append(self._parse_track(item, index))
        next_raw = loaded.get("next")
        next_url = next_raw if isinstance(next_raw, str) and next_raw.strip() != "" else None
        return DeezerTracksPage(tracks=tracks, next_url=next_url)

    def _parse_track(
        self,
        item: Mapping[str, str | int | float | bool | None | Mapping[str, str]],
        index: int,
    ) -> DeezerTrackEntry:
        track_id = item.get("id")
        title = item.get("title")
        if isinstance(track_id, bool) or not isinstance(track_id, int | str):
            raise DeezerApiError(f"deezer track {index} missing id")
        if not isinstance(title, str) or title.strip() == "":
            raise DeezerApiError(f"deezer track {index} missing title")
        artist = self._artist_name(item.get("artist"))
        duration_raw = item.get("duration")
        duration_sec: int | None
        if duration_raw is None:
            duration_sec = None
        elif isinstance(duration_raw, bool) or not isinstance(duration_raw, int | float):
            raise DeezerApiError(f"deezer track {index} duration must be numeric")
        else:
            duration_sec = int(duration_raw)
        return DeezerTrackEntry(
            deezer_id=str(track_id),
            title=title,
            artist=artist,
            duration_sec=duration_sec,
        )

    def _artist_name(
        self,
        artist_raw: str | int | float | bool | None | Mapping[str, str],
    ) -> str:
        if not isinstance(artist_raw, Mapping):
            return ""
        name = artist_raw.get("name")
        return name if isinstance(name, str) else ""
