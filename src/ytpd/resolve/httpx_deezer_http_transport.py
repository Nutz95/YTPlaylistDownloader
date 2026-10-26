import httpx

from ytpd.resolve.deezer_api_error import DeezerApiError

_TIMEOUT_SEC = 30.0


class HttpxDeezerHttpTransport:
    """httpx-backed transport for Deezer short-link and API calls."""

    def __init__(self) -> None:
        self._client = httpx.Client(timeout=_TIMEOUT_SEC, follow_redirects=True)

    def get_text(self, url: str) -> str:
        """GET ``url`` and return the response body text."""
        try:
            response = self._client.get(url)
            response.raise_for_status()
            return response.text
        except httpx.HTTPError as error:
            raise DeezerApiError(f"deezer api request failed: {error}") from error

    def resolve_final_url(self, url: str) -> str:
        """Follow redirects and return the final URL."""
        try:
            response = self._client.head(url)
            if response.status_code >= 400:
                response = self._client.get(url)
            response.raise_for_status()
            return str(response.url)
        except httpx.HTTPError as error:
            raise DeezerApiError(f"deezer short-link resolve failed: {error}") from error

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()
