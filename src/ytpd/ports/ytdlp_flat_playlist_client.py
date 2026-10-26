from typing import Protocol

from ytpd.domain.ytdlp_flat_entry import YtdlpFlatEntry


class YtdlpFlatPlaylistClient(Protocol):
    """Fetch flat YouTube playlist or video metadata without downloading media."""

    def fetch_flat(self, url: str) -> list[YtdlpFlatEntry]:
        """Return flat entries for ``url``."""
