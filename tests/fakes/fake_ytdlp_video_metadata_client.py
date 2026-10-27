from ytpd.domain.ytdlp_video_metadata import YtdlpVideoMetadata
from ytpd.resolve.ytdlp_probe_error import YtdlpProbeError


class FakeYtdlpVideoMetadataClient:
    """Return preloaded video metadata keyed by exact source URL."""

    def __init__(self, metadata_by_url: dict[str, YtdlpVideoMetadata]) -> None:
        self._metadata_by_url = dict(metadata_by_url)

    def fetch_video(self, url: str) -> YtdlpVideoMetadata:
        """Return fixtures for ``url`` or raise when the URL was not configured."""
        try:
            return self._metadata_by_url[url]
        except KeyError as error:
            raise YtdlpProbeError(f"no video fixture for url: {url}") from error
