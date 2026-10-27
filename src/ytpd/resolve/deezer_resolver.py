from ytpd.domain.playlist_resolve_result import PlaylistResolveResult
from ytpd.domain.source_kind import SourceKind
from ytpd.domain.track_phase import TrackPhase
from ytpd.domain.track_ref import TrackRef
from ytpd.ports.deezer_api_client import DeezerApiClient
from ytpd.resolve.deezer_api_error import DeezerApiError


class DeezerResolver:
    """Resolve Deezer playlist URLs into checkpoint-ready tracks."""

    def __init__(self, client: DeezerApiClient) -> None:
        self._client = client

    def resolve(self, url: str, source_kind: SourceKind) -> PlaylistResolveResult:
        """Fetch Deezer tracks for an already-classified Deezer playlist URL."""
        entries = self._client.fetch_playlist_tracks(url)
        if len(entries) == 0:
            raise DeezerApiError("deezer resolve returned no tracks")
        tracks = [
            TrackRef(
                track_id=f"deezer-{entry.deezer_id}",
                title=entry.title,
                artist=entry.artist,
                duration_sec=entry.duration_sec,
                source_kind=source_kind,
                phase=TrackPhase.RESOLVED,
                youtube_url=None,
                deezer_id=entry.deezer_id,
                error_message=None,
            )
            for entry in entries
        ]
        return PlaylistResolveResult(source_kind=source_kind, tracks=tracks)
