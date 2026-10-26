from ytpd.resolve.playlist_resolve_error import PlaylistResolveError


class DeezerApiError(PlaylistResolveError, RuntimeError):
    """Raised when a Deezer API or short-link probe fails."""
