from ytpd.domain.ytdlp_flat_entry import YtdlpFlatEntry
from ytpd.resolve.ytdlp_probe_error import YtdlpProbeError


class FakeYtdlpFlatPlaylistClient:
    """Return preloaded flat entries keyed by exact source URL."""

    def __init__(self, entries_by_url: dict[str, list[YtdlpFlatEntry]]) -> None:
        self._entries_by_url = {
            key: list(value) for key, value in entries_by_url.items()
        }

    def fetch_flat(self, url: str) -> list[YtdlpFlatEntry]:
        """Return fixtures for ``url`` or raise when the URL was not configured."""
        try:
            return list(self._entries_by_url[url])
        except KeyError as error:
            raise YtdlpProbeError(f"no fixture for url: {url}") from error
