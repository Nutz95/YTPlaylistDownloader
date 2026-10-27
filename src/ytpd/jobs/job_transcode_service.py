from dataclasses import replace

from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.job_status import JobStatus
from ytpd.domain.pipeline_stage import PipelineStage
from ytpd.domain.resume_action import ResumeAction
from ytpd.domain.track_phase import TrackPhase
from ytpd.domain.track_ref import TrackRef
from ytpd.domain.transcode_result import TranscodeResult
from ytpd.jobs.invalid_job_error import InvalidJobError
from ytpd.jobs.job_store import JobStore
from ytpd.jobs.track_state_machine import TrackStateMachine
from ytpd.ports.track_artifact_probe import TrackArtifactProbe
from ytpd.transcode.transcode_scheduler import TranscodeScheduler


class JobTranscodeService:
    """Transcode downloaded tracks and persist DONE / ERROR phases."""

    def __init__(
        self,
        job_store: JobStore,
        scheduler: TranscodeScheduler,
        artifact_probe: TrackArtifactProbe,
        state_machine: TrackStateMachine,
    ) -> None:
        self._job_store = job_store
        self._scheduler = scheduler
        self._artifact_probe = artifact_probe
        self._state_machine = state_machine

    def transcode_job(self, job_id: str) -> JobSnapshot:
        """Transcode pending downloaded tracks for ``job_id``."""
        job = self._job_store.get(job_id)
        if job is None:
            raise InvalidJobError("job not found")
        pending = self._pending_tracks(job)
        if len(pending) == 0:
            return job
        job = self._mark_transcoding(job, pending)
        results = self._scheduler.run(job, pending)
        by_id = {item.track_id: item for item in results}
        updated_tracks = [
            self._apply_result(track, by_id.get(track.track_id)) for track in job.tracks
        ]
        return self._job_store.save(
            replace(
                job,
                status=JobStatus.RUNNING,
                pipeline_stage=PipelineStage.TRANSCODE,
                tracks=updated_tracks,
            )
        )

    def _mark_transcoding(
        self,
        job: JobSnapshot,
        pending: list[TrackRef],
    ) -> JobSnapshot:
        pending_ids = {track.track_id for track in pending}
        tracks = [
            replace(track, phase=TrackPhase.TRANSCODING, error_message=None)
            if track.track_id in pending_ids
            else track
            for track in job.tracks
        ]
        return self._job_store.save(
            replace(
                job,
                status=JobStatus.RUNNING,
                pipeline_stage=PipelineStage.TRANSCODE,
                tracks=tracks,
            )
        )

    def _pending_tracks(self, job: JobSnapshot) -> list[TrackRef]:
        pending: list[TrackRef] = []
        for track in job.tracks:
            flags = self._artifact_probe.flags_for(job, track)
            if self._state_machine.decide(track, flags) is ResumeAction.TRANSCODE:
                pending.append(track)
        return pending

    def _apply_result(
        self,
        track: TrackRef,
        result: TranscodeResult | None,
    ) -> TrackRef:
        if result is None:
            return track
        if result.success:
            return replace(track, phase=TrackPhase.DONE, error_message=None)
        return replace(
            track,
            phase=TrackPhase.ERROR,
            error_message=result.error_message,
        )
