from ytpd.domain.ytdlp_flat_entry import YtdlpFlatEntry
from ytpd.resolve.subprocess_ytdlp_json_probe import SubprocessYtdlpJsonProbe
from ytpd.resolve.ytdlp_argv_builder import YtdlpArgvBuilder
from ytpd.resolve.ytdlp_flat_playlist_parser import YtdlpFlatPlaylistParser


class SubprocessYoutubeSearchClient:
    """Search YouTube via ``python -m yt_dlp ytsearchN:query -J``."""

    def __init__(
        self,
        parser: YtdlpFlatPlaylistParser,
        argv_builder: YtdlpArgvBuilder | None = None,
    ) -> None:
        self._probe = SubprocessYtdlpJsonProbe(parser, argv_builder)

    def search(self, query: str, limit: int) -> list[YtdlpFlatEntry]:
        """Return up to ``limit`` flat search hits for ``query``."""
        safe_limit = max(1, limit)
        return self._probe.run(f"ytsearch{safe_limit}:{query}").entries
