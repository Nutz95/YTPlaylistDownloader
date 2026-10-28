from urllib.parse import urlparse

from ytpd.domain.deezer_playlist_snapshot import DeezerPlaylistSnapshot
from ytpd.domain.deezer_track_entry import DeezerTrackEntry
from ytpd.ports.deezer_http_transport import DeezerHttpTransport
from ytpd.resolve.deezer_api_error import DeezerApiError
from ytpd.resolve.deezer_playlist_id_parser import DeezerPlaylistIdParser
from ytpd.resolve.deezer_playlist_title_parser import DeezerPlaylistTitleParser
from ytpd.resolve.deezer_tracks_json_parser import DeezerTracksJsonParser

_MAX_PAGES = 100


class DeezerPlaylistApiClient:
    """Resolve Deezer short links and paginate playlist tracks."""

    def __init__(self, transport: DeezerHttpTransport) -> None:
        self._transport = transport
        self._id_parser = DeezerPlaylistIdParser()
        self._tracks_parser = DeezerTracksJsonParser()
        self._title_parser = DeezerPlaylistTitleParser()

    def fetch_playlist(self, url: str) -> DeezerPlaylistSnapshot:
        """Follow short links when needed, then fetch title and all track pages."""
        playlist_id = self._playlist_id_for(url)
        title = self._title_parser.parse(
            self._transport.get_text(f"https://api.deezer.com/playlist/{playlist_id}")
        )
        tracks = self._fetch_tracks(playlist_id)
        return DeezerPlaylistSnapshot(title=title, tracks=tracks)

    def _fetch_tracks(self, playlist_id: str) -> list[DeezerTrackEntry]:
        page_url: str | None = f"https://api.deezer.com/playlist/{playlist_id}/tracks"
        tracks: list[DeezerTrackEntry] = []
        for _ in range(_MAX_PAGES):
            if page_url is None:
                break
            page = self._tracks_parser.parse_text(self._transport.get_text(page_url))
            tracks.extend(page.tracks)
            page_url = page.next_url
        else:
            raise DeezerApiError("deezer pagination exceeded max pages")
        return tracks

    def _playlist_id_for(self, url: str) -> str:
        host = (urlparse(url).hostname or "").lower()
        if host.endswith("link.deezer.com"):
            return self._id_parser.parse(self._transport.resolve_final_url(url))
        return self._id_parser.parse(url)
