from ytpd.domain.ytdlp_flat_entry import YtdlpFlatEntry


class FakeYoutubeSearchClient:
    """Return preloaded search hits keyed by exact query string."""

    def __init__(self, entries_by_query: dict[str, list[YtdlpFlatEntry]]) -> None:
        self._entries_by_query = {
            key: list(value) for key, value in entries_by_query.items()
        }

    def search(self, query: str, limit: int) -> list[YtdlpFlatEntry]:
        """Return configured hits truncated to ``limit``."""
        entries = self._entries_by_query.get(query, [])
        return list(entries[: max(1, limit)])
