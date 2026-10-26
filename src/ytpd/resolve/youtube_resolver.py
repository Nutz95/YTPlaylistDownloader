from ytpd.domain.playlist_resolve_result import PlaylistResolveResult
from ytpd.domain.source_kind import SourceKind
from ytpd.domain.track_phase import TrackPhase
from ytpd.domain.track_ref import TrackRef
from ytpd.ports.ytdlp_flat_playlist_client import YtdlpFlatPlaylistClient
from ytpd.resolve.ytdlp_probe_error import YtdlpProbeError


class YoutubeResolver:
    """Resolve YouTube playlist or video URLs into checkpoint-ready tracks."""

    def __init__(self, client: YtdlpFlatPlaylistClient) -> None:
        self._client = client

    def resolve(self, url: str, source_kind: SourceKind) -> PlaylistResolveResult:
        """Fetch flat metadata for an already-classified YouTube ``source_kind``."""
        entries = self._client.fetch_flat(url)
        if len(entries) == 0:
            raise YtdlpProbeError("youtube resolve returned no entries")
        tracks = tuple(
            TrackRef(
                track_id=entry.video_id,
                title=entry.title,
                artist=entry.uploader,
                duration_sec=entry.duration_sec,
                source_kind=source_kind,
                phase=TrackPhase.MATCHED,
                youtube_url=entry.webpage_url,
                deezer_id=None,
                error_message=None,
            )
            for entry in entries
        )
        return PlaylistResolveResult(source_kind=source_kind, tracks=tracks)
