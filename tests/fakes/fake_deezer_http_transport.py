from ytpd.resolve.deezer_api_error import DeezerApiError


class FakeDeezerHttpTransport:
    """In-memory HTTP transport for Deezer short-link and pagination tests."""

    def __init__(
        self,
        text_by_url: dict[str, str],
        final_url_by_short: dict[str, str],
    ) -> None:
        self._text_by_url = dict(text_by_url)
        self._final_url_by_short = dict(final_url_by_short)

    def get_text(self, url: str) -> str:
        """Return configured body text for ``url``."""
        try:
            return self._text_by_url[url]
        except KeyError as error:
            raise DeezerApiError(f"no deezer body for url: {url}") from error

    def resolve_final_url(self, url: str) -> str:
        """Return the configured final URL for a short link."""
        try:
            return self._final_url_by_short[url]
        except KeyError as error:
            raise DeezerApiError(f"no deezer redirect for url: {url}") from error
