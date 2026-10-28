from ytpd.domain.deezer_playlist_snapshot import DeezerPlaylistSnapshot
from ytpd.domain.deezer_track_entry import DeezerTrackEntry
from ytpd.resolve.deezer_api_error import DeezerApiError


class FakeDeezerApiClient:
    """Return preloaded Deezer playlists keyed by exact source URL."""

    def __init__(
        self,
        tracks_by_url: dict[str, list[DeezerTrackEntry]],
        titles_by_url: dict[str, str] | None = None,
    ) -> None:
        self._tracks_by_url = {
            key: list(value) for key, value in tracks_by_url.items()
        }
        self._titles_by_url = dict(titles_by_url or {})

    def fetch_playlist(self, url: str) -> DeezerPlaylistSnapshot:
        """Return fixtures for ``url`` or raise when the URL was not configured."""
        try:
            tracks = list(self._tracks_by_url[url])
        except KeyError as error:
            raise DeezerApiError(f"no deezer fixture for url: {url}") from error
        return DeezerPlaylistSnapshot(
            title=self._titles_by_url.get(url),
            tracks=tracks,
        )
