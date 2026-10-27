from ytpd.domain.ytdlp_flat_entry import YtdlpFlatEntry
from ytpd.resolve.subprocess_ytdlp_json_probe import SubprocessYtdlpJsonProbe
from ytpd.resolve.ytdlp_argv_builder import YtdlpArgvBuilder
from ytpd.resolve.ytdlp_flat_playlist_parser import YtdlpFlatPlaylistParser


class SubprocessYtdlpFlatPlaylistClient:
    """Fetch flat playlist metadata via ``python -m yt_dlp``."""

    def __init__(
        self,
        parser: YtdlpFlatPlaylistParser,
        argv_builder: YtdlpArgvBuilder | None = None,
    ) -> None:
        self._probe = SubprocessYtdlpJsonProbe(parser, argv_builder)

    def fetch_flat(self, url: str) -> list[YtdlpFlatEntry]:
        """Run a timed yt-dlp flat JSON probe and parse stdout."""
        return self._probe.run(url)
