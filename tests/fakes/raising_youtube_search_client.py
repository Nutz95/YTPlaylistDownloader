from ytpd.domain.ytdlp_flat_entry import YtdlpFlatEntry
from ytpd.resolve.ytdlp_probe_error import YtdlpProbeError


class RaisingYoutubeSearchClient:
    """Raise ``YtdlpProbeError`` for configured queries; return hits otherwise."""

    def __init__(
        self,
        entries_by_query: dict[str, list[YtdlpFlatEntry]],
        raise_queries: set[str],
    ) -> None:
        self._entries_by_query = {
            key: list(value) for key, value in entries_by_query.items()
        }
        self._raise_queries = set(raise_queries)

    def search(self, query: str, limit: int) -> list[YtdlpFlatEntry]:
        """Return hits or raise when the query is configured to fail."""
        if query in self._raise_queries:
            raise YtdlpProbeError("simulated search failure")
        entries = self._entries_by_query.get(query, [])
        return list(entries[: max(1, limit)])
