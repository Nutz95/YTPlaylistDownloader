from ytpd.domain.ytdlp_flat_entry import YtdlpFlatEntry
from ytpd.domain.ytdlp_flat_playlist_result import YtdlpFlatPlaylistResult
from ytpd.resolve.ytdlp_probe_error import YtdlpProbeError


class FakeYtdlpFlatPlaylistClient:
    """Return preloaded flat playlist results keyed by exact source URL."""

    def __init__(
        self,
        entries_by_url: dict[str, list[YtdlpFlatEntry]],
        titles_by_url: dict[str, str] | None = None,
    ) -> None:
        self._entries_by_url = {
            key: list(value) for key, value in entries_by_url.items()
        }
        self._titles_by_url = dict(titles_by_url or {})

    def fetch_flat(self, url: str) -> YtdlpFlatPlaylistResult:
        """Return fixtures for ``url`` or raise when the URL was not configured."""
        try:
            entries = list(self._entries_by_url[url])
        except KeyError as error:
            raise YtdlpProbeError(f"no fixture for url: {url}") from error
        return YtdlpFlatPlaylistResult(
            title=self._titles_by_url.get(url),
            entries=entries,
        )
