from typing import Protocol

from ytpd.domain.ytdlp_flat_entry import YtdlpFlatEntry


class YoutubeSearchClient(Protocol):
    """Search YouTube for candidate videos without downloading media."""

    def search(self, query: str, limit: int) -> list[YtdlpFlatEntry]:
        """Return up to ``limit`` flat search hits for ``query``."""
