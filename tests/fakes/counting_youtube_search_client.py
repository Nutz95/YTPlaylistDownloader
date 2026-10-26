from ytpd.domain.ytdlp_flat_entry import YtdlpFlatEntry
from ytpd.ports.youtube_search_client import YoutubeSearchClient


class CountingYoutubeSearchClient:
    """Delegate to another search client while counting ``search`` calls."""

    def __init__(self, inner: YoutubeSearchClient) -> None:
        self._inner = inner
        self.search_calls = 0

    def search(self, query: str, limit: int) -> list[YtdlpFlatEntry]:
        """Forward to the inner client and increment the call counter."""
        self.search_calls += 1
        return self._inner.search(query, limit)
