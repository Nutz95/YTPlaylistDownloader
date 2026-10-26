from urllib.parse import parse_qs, urlparse

from ytpd.domain.source_kind import SourceKind
from ytpd.resolve.unsupported_source_url_error import UnsupportedSourceUrlError


class UrlClassifier:
    """Classify a playlist or media URL into a ``SourceKind``."""

    def classify(self, url: str) -> SourceKind:
        """Return the source kind for ``url`` or raise when unsupported."""
        cleaned = url.strip()
        if cleaned == "":
            raise UnsupportedSourceUrlError("url must be a non-empty string")
        parsed = urlparse(cleaned)
        host = (parsed.hostname or "").lower()
        if host.endswith("deezer.com") or host == "link.deezer.com":
            return SourceKind.DEEZER_PLAYLIST
        if host in {"youtu.be", "www.youtu.be"}:
            return SourceKind.YOUTUBE_VIDEO
        if host.endswith("youtube.com") or host.endswith("youtube-nocookie.com"):
            query = parse_qs(parsed.query)
            if "list" in query:
                return SourceKind.YOUTUBE_PLAYLIST
            return SourceKind.YOUTUBE_VIDEO
        raise UnsupportedSourceUrlError(f"unsupported url host: {host or '(missing)'}")
