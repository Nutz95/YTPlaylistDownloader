from ytpd.domain.deezer_track_entry import DeezerTrackEntry
from ytpd.resolve.deezer_api_error import DeezerApiError


class FakeDeezerApiClient:
    """Return preloaded Deezer tracks keyed by exact source URL."""

    def __init__(self, tracks_by_url: dict[str, list[DeezerTrackEntry]]) -> None:
        self._tracks_by_url = {
            key: list(value) for key, value in tracks_by_url.items()
        }

    def fetch_playlist_tracks(self, url: str) -> list[DeezerTrackEntry]:
        """Return fixtures for ``url`` or raise when the URL was not configured."""
        try:
            return list(self._tracks_by_url[url])
        except KeyError as error:
            raise DeezerApiError(f"no deezer fixture for url: {url}") from error
