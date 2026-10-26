from ytpd.resolve.playlist_resolve_error import PlaylistResolveError


class UnsupportedSourceUrlError(PlaylistResolveError, ValueError):
    """Raised when a source URL cannot be classified or routed."""
