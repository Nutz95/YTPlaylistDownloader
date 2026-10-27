import json
import subprocess

from ytpd.domain.ytdlp_video_metadata import YtdlpVideoMetadata
from ytpd.resolve.ytdlp_argv_builder import YtdlpArgvBuilder
from ytpd.resolve.ytdlp_probe_error import YtdlpProbeError
from ytpd.resolve.ytdlp_video_metadata_parser import YtdlpVideoMetadataParser
from ytpd.runtime.subprocess_text_runner import SubprocessTextRunner

_PROBE_TIMEOUT_SEC = 120.0


class SubprocessYtdlpVideoMetadataProbe:
    """Run ``python -m yt_dlp --no-download -J`` (non-flat) for chapter metadata."""

    def __init__(
        self,
        parser: YtdlpVideoMetadataParser,
        argv_builder: YtdlpArgvBuilder | None = None,
    ) -> None:
        self._parser = parser
        self._runner = SubprocessTextRunner()
        self._argv_builder = argv_builder or YtdlpArgvBuilder()

    def run(self, url: str) -> YtdlpVideoMetadata:
        """Probe ``url`` and parse full video JSON including chapters."""
        try:
            completed = self._runner.run(
                [
                    *self._argv_builder.prefix(),
                    "--no-download",
                    "-J",
                    url,
                ],
                _PROBE_TIMEOUT_SEC,
            )
        except OSError as error:
            raise YtdlpProbeError(f"yt-dlp is not available: {error}") from error
        except subprocess.TimeoutExpired as error:
            raise YtdlpProbeError("yt-dlp probe timed out") from error
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip() or "unknown"
            raise YtdlpProbeError(f"yt-dlp failed: {detail}")
        try:
            return self._parser.parse(completed.stdout)
        except (json.JSONDecodeError, YtdlpProbeError) as error:
            raise YtdlpProbeError(str(error)) from error
