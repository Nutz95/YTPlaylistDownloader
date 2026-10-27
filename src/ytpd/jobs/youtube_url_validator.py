from urllib.parse import urlparse


class YoutubeUrlValidator:
    """Validate that a string is a usable YouTube watch URL."""

    def normalize(self, raw_url: str) -> str | None:
        """Return a cleaned URL, or ``None`` when it is not a YouTube watch link."""
        cleaned = raw_url.strip()
        if cleaned == "":
            return None
        parsed = urlparse(cleaned)
        host = parsed.netloc.casefold()
        if host.startswith("www."):
            host = host[4:]
        if host in {"youtu.be"}:
            video_id = parsed.path.lstrip("/").split("/")[0]
            if video_id == "":
                return None
            return f"https://www.youtube.com/watch?v={video_id}"
        if host in {"youtube.com", "m.youtube.com", "music.youtube.com"}:
            if parsed.path not in {"/watch", "/watch/"}:
                if parsed.path.startswith("/shorts/"):
                    video_id = parsed.path.removeprefix("/shorts/").split("/")[0]
                    if video_id == "":
                        return None
                    return f"https://www.youtube.com/watch?v={video_id}"
                return None
            query = parsed.query
            for part in query.split("&"):
                if part.startswith("v=") and len(part) > 2:
                    video_id = part[2:]
                    if video_id.strip() != "":
                        return f"https://www.youtube.com/watch?v={video_id}"
            return None
        return None
