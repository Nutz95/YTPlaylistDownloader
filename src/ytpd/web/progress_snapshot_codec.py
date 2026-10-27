from typing import cast

from ytpd.domain.media_progress import MediaProgress
from ytpd.domain.progress_snapshot import ProgressSnapshot
from ytpd.web.media_progress_json_payload import MediaProgressJsonPayload
from ytpd.web.progress_snapshot_json_payload import ProgressSnapshotJsonPayload
from ytpd.web.track_phase_name import TrackPhaseName


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
            "stage": snapshot.global_progress.stage,
            "stage_done": snapshot.global_progress.stage_done,
            "stage_total": snapshot.global_progress.stage_total,
            "active_media": [
                self._media_to_payload(media) for media in snapshot.active_media
            ],
            "failed_media": [
                self._media_to_payload(media) for media in snapshot.failed_media
            ],
        }

    def _media_to_payload(self, media: MediaProgress) -> MediaProgressJsonPayload:
        return {
            "track_id": media.track_id,
            "title": media.title,
            "artist": media.artist,
            "phase_label": cast(TrackPhaseName, media.phase.value),
            "detail": media.detail,
            "candidates": [
                {
                    "youtube_url": candidate.youtube_url,
                    "title": candidate.title,
                    "channel": candidate.channel,
                    "duration_sec": candidate.duration_sec,
                }
                for candidate in media.candidates
            ],
        }
