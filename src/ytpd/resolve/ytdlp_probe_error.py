from ytpd.resolve.playlist_resolve_error import PlaylistResolveError


class YtdlpProbeError(PlaylistResolveError, RuntimeError):
    """Raised when a yt-dlp flat-playlist probe fails."""
