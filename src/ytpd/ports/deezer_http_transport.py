from typing import Protocol


class DeezerHttpTransport(Protocol):
    """Minimal HTTP operations required by the Deezer playlist client."""

    def get_text(self, url: str) -> str:
        """GET ``url`` and return the response body text."""

    def resolve_final_url(self, url: str) -> str:
        """Follow redirects and return the final URL."""
