import re
from urllib.parse import urlparse

from ytpd.resolve.deezer_api_error import DeezerApiError

_PLAYLIST_PATH = re.compile(r"/playlist/(\d+)", re.IGNORECASE)


class DeezerPlaylistIdParser:
    """Extract a numeric Deezer playlist id from a long URL."""

    def parse(self, url: str) -> str:
        """Return the playlist id embedded in ``url``."""
        parsed = urlparse(url.strip())
        match = _PLAYLIST_PATH.search(parsed.path)
        if match is None:
            raise DeezerApiError(f"deezer playlist id not found in url: {url}")
        return match.group(1)
