from dataclasses import dataclass

from ytpd.domain.ytdlp_flat_entry import YtdlpFlatEntry


@dataclass(frozen=True)
class YtdlpFlatPlaylistResult:
    """Flat yt-dlp playlist (or search) payload: optional title plus entries."""

    title: str | None
    entries: list[YtdlpFlatEntry]
