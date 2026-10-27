import json
import subprocess

from ytpd.domain.ytdlp_flat_entry import YtdlpFlatEntry
from ytpd.resolve.ytdlp_argv_builder import YtdlpArgvBuilder
from ytpd.resolve.ytdlp_flat_playlist_parser import YtdlpFlatPlaylistParser
from ytpd.resolve.ytdlp_probe_error import YtdlpProbeError
from ytpd.runtime.subprocess_text_runner import SubprocessTextRunner

_PROBE_TIMEOUT_SEC = 120.0


class SubprocessYtdlpJsonProbe:
    """Run ``python -m yt_dlp ... -J`` and parse flat playlist JSON from stdout."""

    def __init__(
        self,
        parser: YtdlpFlatPlaylistParser,
        argv_builder: YtdlpArgvBuilder | None = None,
    ) -> None:
        self._parser = parser
        self._runner = SubprocessTextRunner()
        self._argv_builder = argv_builder or YtdlpArgvBuilder()

    def run(self, target: str) -> list[YtdlpFlatEntry]:
        """Probe ``target`` (URL or ``ytsearchN:query``) with flat JSON output."""
        try:
            completed = self._runner.run(
                [
                    *self._argv_builder.prefix(),
                    "--flat-playlist",
                    "--no-download",
                    "-J",
                    target,
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
