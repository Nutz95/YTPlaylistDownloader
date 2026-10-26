from ytpd.domain.media_progress import MediaProgress
from ytpd.domain.progress_snapshot import ProgressSnapshot
from ytpd.web.media_progress_json_payload import MediaProgressJsonPayload
from ytpd.web.progress_snapshot_json_payload import ProgressSnapshotJsonPayload


class ProgressSnapshotCodec:
    """Convert progress snapshots to the API JSON contract."""

    def to_payload(self, snapshot: ProgressSnapshot) -> ProgressSnapshotJsonPayload:
        """Serialize a progress snapshot for HTTP responses."""
        return {
            "job_id": snapshot.job_id,
            "percent": snapshot.global_progress.percent,
            "completed_tracks": snapshot.global_progress.completed_tracks,
            "total_tracks": snapshot.global_progress.total_tracks,
            "label": snapshot.global_progress.label,
            "active_media": [
                self._media_to_payload(media) for media in snapshot.active_media
            ],
        }

    def _media_to_payload(self, media: MediaProgress) -> MediaProgressJsonPayload:
        return {
            "track_id": media.track_id,
            "title": media.title,
            "phase_label": media.phase_label,
            "detail": media.detail,
        }
