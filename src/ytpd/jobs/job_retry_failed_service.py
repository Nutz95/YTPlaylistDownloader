from dataclasses import replace

from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.job_status import JobStatus
from ytpd.domain.track_phase import TrackPhase
from ytpd.domain.track_ref import TrackRef
from ytpd.jobs.invalid_job_error import InvalidJobError
from ytpd.jobs.job_store import JobStore
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths
from ytpd.ports.track_artifact_probe import TrackArtifactProbe

_FAILED = frozenset({TrackPhase.MATCH_FAILED, TrackPhase.ERROR})


class JobRetryFailedService:
    """Reset failed tracks so a later pipeline run can retry them."""

    def __init__(
        self,
        job_store: JobStore,
        artifact_probe: TrackArtifactProbe,
        paths: TrackArtifactPaths,
    ) -> None:
        self._job_store = job_store
        self._artifact_probe = artifact_probe
        self._paths = paths

    def retry_failed(self, job_id: str) -> JobSnapshot:
        """Reset MATCH_FAILED / ERROR tracks to the previous actionable phase."""
        job = self._job_store.get(job_id)
        if job is None:
            raise InvalidJobError("job not found")
        if job.status is JobStatus.RUNNING:
            raise InvalidJobError("stop the running pipeline before retrying failures")
        tracks: list[TrackRef] = []
        reset_count = 0
        for track in job.tracks:
            if track.phase not in _FAILED:
                tracks.append(track)
                continue
            tracks.append(self._reset_track(job, track))
            reset_count += 1
        if reset_count == 0:
            raise InvalidJobError("job has no failed tracks to retry")
        return self._job_store.save(
            replace(
                job,
                status=JobStatus.INTERRUPTED,
                pipeline_stage=None,
                error_message=None,
                tracks=tracks,
            )
        )

    def _reset_track(self, job: JobSnapshot, track: TrackRef) -> TrackRef:
        if track.phase is TrackPhase.MATCH_FAILED:
            return replace(
                track,
                phase=TrackPhase.RESOLVED,
                youtube_url=None,
                error_message=None,
            )
        flags = self._artifact_probe.flags_for(job, track)
        if flags.download_complete:
            return replace(track, phase=TrackPhase.DOWNLOADED, error_message=None)
        if track.youtube_url is not None and track.youtube_url.strip() != "":
            return replace(track, phase=TrackPhase.MATCHED, error_message=None)
        return replace(
            track,
            phase=TrackPhase.RESOLVED,
            youtube_url=None,
            error_message=None,
        )
