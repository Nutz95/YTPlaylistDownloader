from dataclasses import replace

from ytpd.domain.download_result import DownloadResult
from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.job_status import JobStatus
from ytpd.domain.pipeline_stage import PipelineStage
from ytpd.domain.resume_action import ResumeAction
from ytpd.domain.track_phase import TrackPhase
from ytpd.domain.track_ref import TrackRef
from ytpd.download.download_pool import DownloadPool
from ytpd.jobs.invalid_job_error import InvalidJobError
from ytpd.jobs.job_cancel_flag import JobCancelFlag
from ytpd.jobs.job_failure_log import JobFailureLog
from ytpd.jobs.job_store import JobStore
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths
from ytpd.jobs.track_phase_healer import TrackPhaseHealer
from ytpd.jobs.track_state_machine import TrackStateMachine
from ytpd.ports.track_artifact_probe import TrackArtifactProbe


class JobDownloadService:
    """Download matched tracks in parallel and persist phase updates."""

    def __init__(
        self,
        job_store: JobStore,
        download_pool: DownloadPool,
        artifact_probe: TrackArtifactProbe,
        state_machine: TrackStateMachine,
        paths: TrackArtifactPaths,
        cancel_flag: JobCancelFlag,
        failure_log: JobFailureLog,
        phase_healer: TrackPhaseHealer,
    ) -> None:
        self._job_store = job_store
        self._download_pool = download_pool
        self._artifact_probe = artifact_probe
        self._state_machine = state_machine
        self._paths = paths
        self._cancel_flag = cancel_flag
        self._failure_log = failure_log
        self._phase_healer = phase_healer

    def download_job(self, job_id: str) -> JobSnapshot:
        """Download pending matched tracks for ``job_id`` and save results."""
        job = self._job_store.get(job_id)
        if job is None:
            raise InvalidJobError("job not found")
        if self._cancel_flag.is_cancelled():
            return job
        healed = self._phase_healer.heal(job)
        pending = self._pending_tracks(healed)
        if len(pending) == 0:
            if healed is job:
                return job
            return self._job_store.save(
                replace(
                    healed,
                    status=self._status_for_save(),
                    pipeline_stage=PipelineStage.DOWNLOAD,
                )
            )
        job = self._mark_downloading(healed, pending)
        for result in self._download_pool.iter_results(job, pending):
            job = self._apply_and_save(job, result)
            if self._cancel_flag.is_cancelled():
                break
        return job

    def _mark_downloading(
        self,
        job: JobSnapshot,
        pending: list[TrackRef],
    ) -> JobSnapshot:
        pending_ids = {track.track_id for track in pending}
        tracks = [
            replace(track, phase=TrackPhase.DOWNLOADING, error_message=None)
            if track.track_id in pending_ids
            else track
            for track in job.tracks
        ]
        return self._job_store.save(
            replace(
                job,
                status=self._status_for_save(),
                pipeline_stage=PipelineStage.DOWNLOAD,
                tracks=tracks,
            )
        )

    def _pending_tracks(self, job: JobSnapshot) -> list[TrackRef]:
        pending: list[TrackRef] = []
        for track in job.tracks:
            flags = self._artifact_probe.flags_for(job, track)
            action = self._state_machine.decide(track, flags)
            if action is ResumeAction.DOWNLOAD:
                pending.append(track)
        return pending

    def _apply_and_save(self, job: JobSnapshot, result: DownloadResult) -> JobSnapshot:
        updated_tracks = [
            self._apply_result(job, track, result if track.track_id == result.track_id else None)
            for track in job.tracks
        ]
        saved = self._job_store.save(
            replace(
                job,
                status=self._status_for_save(),
                pipeline_stage=PipelineStage.DOWNLOAD,
                tracks=updated_tracks,
            )
        )
        for track in saved.tracks:
            if track.track_id != result.track_id:
                continue
            if track.phase is TrackPhase.ERROR and track.error_message:
                self._failure_log.append(saved, track, track.error_message)
        return saved

    def _status_for_save(self) -> JobStatus:
        if self._cancel_flag.is_cancelled():
            return JobStatus.CANCELLED
        return JobStatus.RUNNING

    def _apply_result(
        self,
        job: JobSnapshot,
        track: TrackRef,
        result: DownloadResult | None,
    ) -> TrackRef:
        if result is None:
            return track
        if result.success:
            marker = self._paths.download_complete_marker(job, track)
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text("ok", encoding="utf-8")
            return replace(
                track,
                phase=TrackPhase.DOWNLOADED,
                error_message=None,
            )
        return replace(
            track,
            phase=TrackPhase.ERROR,
            error_message=result.error_message,
        )
