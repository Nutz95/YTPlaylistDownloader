from dataclasses import replace

from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.job_status import JobStatus
from ytpd.domain.track_phase import TrackPhase
from ytpd.domain.track_ref import TrackRef
from ytpd.jobs.job_store import JobStore


class JobCancelFinalizer:
    """Persist CANCELLED status and freeze in-flight track phases for retry."""

    def __init__(self, job_store: JobStore) -> None:
        self._job_store = job_store

    def finalize(self, job_id: str) -> JobSnapshot | None:
        """Mark ``job_id`` cancelled and clear active working phases."""
        job = self._job_store.get(job_id)
        if job is None:
            return None
        tracks = [self._freeze_track(track) for track in job.tracks]
        return self._job_store.save(
            replace(
                job,
                status=JobStatus.CANCELLED,
                pipeline_stage=None,
                error_message="cancelled by user",
                tracks=tracks,
            )
        )

    def _freeze_track(self, track: TrackRef) -> TrackRef:
        if track.phase is TrackPhase.MATCHING:
            return replace(track, phase=TrackPhase.RESOLVED, error_message=None)
        if track.phase is TrackPhase.DOWNLOADING:
            if track.youtube_url is not None and track.youtube_url.strip() != "":
                return replace(track, phase=TrackPhase.MATCHED, error_message=None)
            return replace(track, phase=TrackPhase.RESOLVED, error_message=None)
        if track.phase is TrackPhase.TRANSCODING:
            return replace(track, phase=TrackPhase.DOWNLOADED, error_message=None)
        return track
