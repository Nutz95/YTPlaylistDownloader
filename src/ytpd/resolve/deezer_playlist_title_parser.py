import json

from ytpd.resolve.deezer_api_error import DeezerApiError


class DeezerPlaylistTitleParser:
    """Parse the playlist title from a Deezer playlist metadata JSON body."""

    def parse(self, text: str) -> str | None:
        """Return the playlist title when present and non-empty."""
        try:
            loaded = json.loads(text)
        except json.JSONDecodeError as error:
            raise DeezerApiError("deezer playlist metadata is not valid JSON") from error
        if not isinstance(loaded, dict):
            raise DeezerApiError("deezer playlist metadata must be an object")
        title = loaded.get("title")
        if not isinstance(title, str) or title.strip() == "":
            return None
        return title.strip()
