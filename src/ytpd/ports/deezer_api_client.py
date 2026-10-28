from typing import Protocol

from ytpd.domain.deezer_playlist_snapshot import DeezerPlaylistSnapshot


class DeezerApiClient(Protocol):
    """Fetch Deezer playlist metadata and tracks, including short-link resolution."""

    def fetch_playlist(self, url: str) -> DeezerPlaylistSnapshot:
        """Return title plus all tracks for a Deezer playlist URL."""
