from ytpd.domain.ytdlp_video_metadata import YtdlpVideoMetadata
from ytpd.resolve.subprocess_ytdlp_video_metadata_probe import (
    SubprocessYtdlpVideoMetadataProbe,
)
from ytpd.resolve.ytdlp_argv_builder import YtdlpArgvBuilder
from ytpd.resolve.ytdlp_video_metadata_parser import YtdlpVideoMetadataParser


class SubprocessYtdlpVideoMetadataClient:
    """Fetch non-flat video metadata via ``python -m yt_dlp``."""

    def __init__(
        self,
        parser: YtdlpVideoMetadataParser,
        argv_builder: YtdlpArgvBuilder | None = None,
    ) -> None:
        self._probe = SubprocessYtdlpVideoMetadataProbe(parser, argv_builder)

    def fetch_video(self, url: str) -> YtdlpVideoMetadata:
        """Run a timed yt-dlp JSON probe and parse video metadata."""
        return self._probe.run(url)
