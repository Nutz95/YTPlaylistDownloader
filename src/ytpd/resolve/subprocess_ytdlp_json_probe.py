import json
import subprocess
import sys

from ytpd.domain.ytdlp_flat_entry import YtdlpFlatEntry
from ytpd.resolve.ytdlp_flat_playlist_parser import YtdlpFlatPlaylistParser
from ytpd.resolve.ytdlp_probe_error import YtdlpProbeError

_PROBE_TIMEOUT_SEC = 120.0


class SubprocessYtdlpJsonProbe:
    """Run ``python -m yt_dlp ... -J`` and parse flat playlist JSON from stdout."""

    def __init__(self, parser: YtdlpFlatPlaylistParser) -> None:
        self._parser = parser

    def run(self, target: str) -> list[YtdlpFlatEntry]:
        """Probe ``target`` (URL or ``ytsearchN:query``) with flat JSON output."""
        try:
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "yt_dlp",
                    "--flat-playlist",
                    "--no-download",
                    "-J",
                    target,
                ],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=_PROBE_TIMEOUT_SEC,
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
