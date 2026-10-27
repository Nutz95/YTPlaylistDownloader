from ytpd.domain.playlist_resolve_result import PlaylistResolveResult
from ytpd.domain.source_kind import SourceKind
from ytpd.domain.track_phase import TrackPhase
from ytpd.domain.track_ref import TrackRef
from ytpd.domain.ytdlp_flat_entry import YtdlpFlatEntry
from ytpd.domain.ytdlp_video_metadata import YtdlpVideoMetadata
from ytpd.ports.ytdlp_flat_playlist_client import YtdlpFlatPlaylistClient
from ytpd.ports.ytdlp_video_metadata_client import YtdlpVideoMetadataClient
from ytpd.resolve.ytdlp_probe_error import YtdlpProbeError

_MIN_CHAPTERS_TO_EXPAND = 2


class YoutubeResolver:
    """Resolve YouTube playlist or video URLs into checkpoint-ready tracks."""

    def __init__(
        self,
        flat_client: YtdlpFlatPlaylistClient,
        video_client: YtdlpVideoMetadataClient,
    ) -> None:
        self._flat_client = flat_client
        self._video_client = video_client

    def resolve(self, url: str, source_kind: SourceKind) -> PlaylistResolveResult:
        """Fetch metadata and expand chaptered videos into one track per chapter."""
        if source_kind is SourceKind.YOUTUBE_VIDEO:
            return self._resolve_video(url, source_kind)
        entries = self._flat_client.fetch_flat(url)
        if len(entries) == 0:
            raise YtdlpProbeError("youtube resolve returned no entries")
        tracks = [self._track_from_flat_entry(entry, source_kind) for entry in entries]
        return PlaylistResolveResult(source_kind=source_kind, tracks=tracks)

    def _resolve_video(
        self,
        url: str,
        source_kind: SourceKind,
    ) -> PlaylistResolveResult:
        metadata = self._video_client.fetch_video(url)
        if len(metadata.chapters) >= _MIN_CHAPTERS_TO_EXPAND:
            tracks = self._tracks_from_chapters(metadata, source_kind)
        else:
            tracks = [self._track_from_video_metadata(metadata, source_kind)]
        return PlaylistResolveResult(source_kind=source_kind, tracks=tracks)

    def _tracks_from_chapters(
        self,
        metadata: YtdlpVideoMetadata,
        source_kind: SourceKind,
    ) -> list[TrackRef]:
        tracks: list[TrackRef] = []
        for index, chapter in enumerate(metadata.chapters):
            duration_sec = int(round(chapter.end_sec - chapter.start_sec))
            tracks.append(
                TrackRef(
                    track_id=f"{metadata.video_id}__ch{index:02d}",
                    title=chapter.title,
                    artist=metadata.uploader,
                    duration_sec=duration_sec,
                    source_kind=source_kind,
                    phase=TrackPhase.MATCHED,
                    youtube_url=metadata.webpage_url,
                    deezer_id=None,
                    error_message=None,
                    chapter_start_sec=chapter.start_sec,
                    chapter_end_sec=chapter.end_sec,
                    parent_video_id=metadata.video_id,
                    chapter_index=index,
                )
            )
        return tracks

    def _track_from_video_metadata(
        self,
        metadata: YtdlpVideoMetadata,
        source_kind: SourceKind,
    ) -> TrackRef:
        return TrackRef(
            track_id=metadata.video_id,
            title=metadata.title,
            artist=metadata.uploader,
            duration_sec=metadata.duration_sec,
            source_kind=source_kind,
            phase=TrackPhase.MATCHED,
            youtube_url=metadata.webpage_url,
            deezer_id=None,
            error_message=None,
        )

    def _track_from_flat_entry(
        self,
        entry: YtdlpFlatEntry,
        source_kind: SourceKind,
    ) -> TrackRef:
        return TrackRef(
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
