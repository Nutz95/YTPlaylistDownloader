import json

from ytpd.domain.deezer_track_entry import DeezerTrackEntry
from ytpd.resolve.deezer_api_error import DeezerApiError
from ytpd.resolve.deezer_artist_json import DeezerArtistJson
from ytpd.resolve.deezer_track_json import DeezerTrackJson
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
            tracks.append(self._parse_track(self._as_track_json(item, index), index))
        next_raw = loaded.get("next")
        next_url = next_raw if isinstance(next_raw, str) and next_raw.strip() != "" else None
        return DeezerTracksPage(tracks=tracks, next_url=next_url)

    def _as_track_json(
        self,
        item: dict[str, str | int | float | bool | None | DeezerArtistJson],
        index: int,
    ) -> DeezerTrackJson:
        track_id = item.get("id")
        title = item.get("title")
        if isinstance(track_id, bool) or not isinstance(track_id, int | str):
            raise DeezerApiError(f"deezer track {index} missing id")
        if not isinstance(title, str) or title.strip() == "":
            raise DeezerApiError(f"deezer track {index} missing title")
        payload: DeezerTrackJson = {"id": track_id, "title": title}
        artist_raw = item.get("artist")
        if isinstance(artist_raw, dict):
            name = artist_raw.get("name")
            if isinstance(name, str):
                artist: DeezerArtistJson = {"name": name}
                payload["artist"] = artist
        duration_raw = item.get("duration")
        if isinstance(duration_raw, bool):
            raise DeezerApiError(f"deezer track {index} duration must be numeric")
        if isinstance(duration_raw, int | float):
            payload["duration"] = duration_raw
        elif duration_raw is not None:
            raise DeezerApiError(f"deezer track {index} duration must be numeric")
        return payload

    def _parse_track(self, item: DeezerTrackJson, index: int) -> DeezerTrackEntry:
        artist = ""
        if "artist" in item:
            artist = item["artist"].get("name", "")
        duration_sec: int | None = None
        if "duration" in item:
            duration_sec = int(item["duration"])
        return DeezerTrackEntry(
            deezer_id=str(item["id"]),
            title=item["title"],
            artist=artist,
            duration_sec=duration_sec,
        )
