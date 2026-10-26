from typing import Protocol

from ytpd.domain.deezer_track_entry import DeezerTrackEntry


class DeezerApiClient(Protocol):
    """Fetch Deezer playlist tracks, including short-link resolution."""

    def fetch_playlist_tracks(self, url: str) -> list[DeezerTrackEntry]:
        """Return all tracks for a Deezer playlist URL (paginated)."""
