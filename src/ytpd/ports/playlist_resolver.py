from typing import Protocol

from ytpd.domain.playlist_resolve_result import PlaylistResolveResult


class PlaylistResolver(Protocol):
    """Resolve a source URL into typed track metadata."""

    def resolve(self, url: str) -> PlaylistResolveResult:
        """Resolve ``url`` into a source kind and track list."""
