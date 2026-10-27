from typing import Protocol

from ytpd.domain.ytdlp_video_metadata import YtdlpVideoMetadata


class YtdlpVideoMetadataClient(Protocol):
    """Fetch full YouTube video metadata including chapters."""

    def fetch_video(self, url: str) -> YtdlpVideoMetadata:
        """Return non-flat metadata for a single video ``url``."""
