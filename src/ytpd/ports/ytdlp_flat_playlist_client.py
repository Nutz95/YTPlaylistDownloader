from typing import Protocol

from ytpd.domain.ytdlp_flat_playlist_result import YtdlpFlatPlaylistResult


class YtdlpFlatPlaylistClient(Protocol):
    """Fetch flat YouTube playlist or video metadata without downloading media."""

    def fetch_flat(self, url: str) -> YtdlpFlatPlaylistResult:
        """Return titled flat entries for ``url``."""
