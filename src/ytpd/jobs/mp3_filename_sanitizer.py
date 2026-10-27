import re

_INVALID_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_MULTI_SPACE = re.compile(r"\s+")
_MAX_STEM_LEN = 120


class Mp3FilenameSanitizer:
    """Build Windows-safe MP3 file name stems from artist and title."""

    def sanitize(self, title: str) -> str:
        """Return a filesystem-safe stem fragment, falling back to ``track``."""
        cleaned = self._clean(title)
        if cleaned == "":
            return "track"
        return cleaned[:_MAX_STEM_LEN]

    def stem_for_track(self, artist: str, title: str, fallback_id: str) -> str:
        """Return ``Artist - Title``, or a sensible fallback when parts are empty."""
        artist_part = self._clean(artist)
        title_part = self._clean(title)
        if artist_part != "" and title_part != "":
            stem = f"{artist_part} - {title_part}"
        elif title_part != "":
            stem = title_part
        elif artist_part != "":
            stem = artist_part
        else:
            stem = self._clean(fallback_id) or "track"
        return stem[:_MAX_STEM_LEN].strip(" .") or "track"

    def _clean(self, value: str) -> str:
        cleaned = _INVALID_CHARS.sub(" ", value)
        return _MULTI_SPACE.sub(" ", cleaned).strip(" .")
