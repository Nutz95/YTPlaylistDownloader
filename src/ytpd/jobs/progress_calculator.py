from ytpd.domain.global_progress import GlobalProgress
from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.media_progress import MediaProgress
from ytpd.domain.progress_snapshot import ProgressSnapshot
from ytpd.domain.track_phase import TrackPhase
from ytpd.domain.track_ref import TrackRef

_DONE_PHASES = frozenset({TrackPhase.DONE, TrackPhase.SKIPPED})
_ACTIVE_PHASES = frozenset({TrackPhase.DOWNLOADING, TrackPhase.TRANSCODING})


class ProgressCalculator:
    """Build a progress snapshot from a job snapshot."""

    def from_job(self, job: JobSnapshot) -> ProgressSnapshot:
        """Compute global and active-media progress for ``job``."""
        total = len(job.tracks)
        completed = sum(1 for track in job.tracks if track.phase in _DONE_PHASES)
        percent = 0.0 if total == 0 else (completed / total) * 100.0
        return ProgressSnapshot(
            job_id=job.job_id,
            global_progress=GlobalProgress(
                percent=percent,
                completed_tracks=completed,
                total_tracks=total,
                label=job.status.value,
            ),
            active_media=[
                self._active_media(track)
                for track in job.tracks
                if track.phase in _ACTIVE_PHASES
            ],
        )

    def _active_media(self, track: TrackRef) -> MediaProgress:
        return MediaProgress(
            track_id=track.track_id,
            title=track.title,
            phase=track.phase,
            detail=track.error_message or "",
        )
