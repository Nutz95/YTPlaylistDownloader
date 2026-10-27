import threading
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import replace

from ytpd.domain.download_result import DownloadResult
from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.job_status import JobStatus
from ytpd.domain.pipeline_stage import PipelineStage
from ytpd.domain.resume_action import ResumeAction
from ytpd.domain.track_phase import TrackPhase
from ytpd.domain.track_ref import TrackRef
from ytpd.domain.transcode_result import TranscodeResult
from ytpd.download.download_pool import DownloadPool
from ytpd.jobs.invalid_job_error import InvalidJobError
from ytpd.jobs.job_cancel_flag import JobCancelFlag
from ytpd.jobs.job_failure_log import JobFailureLog
from ytpd.jobs.job_store import JobStore
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths
from ytpd.jobs.track_phase_healer import TrackPhaseHealer
from ytpd.jobs.track_state_machine import TrackStateMachine
from ytpd.ports.track_artifact_probe import TrackArtifactProbe
from ytpd.transcode.transcode_scheduler import TranscodeScheduler


class JobDownloadTranscodeCoordinator:
    """Download tracks and start transcoding each as soon as its media is ready."""

    def __init__(
        self,
        job_store: JobStore,
        download_pool: DownloadPool,
        scheduler: TranscodeScheduler,
        artifact_probe: TrackArtifactProbe,
        state_machine: TrackStateMachine,
        paths: TrackArtifactPaths,
        cancel_flag: JobCancelFlag,
        failure_log: JobFailureLog,
        phase_healer: TrackPhaseHealer,
        transcode_pool_workers: int | None = None,
    ) -> None:
        self._job_store = job_store
        self._download_pool = download_pool
        self._scheduler = scheduler
        self._artifact_probe = artifact_probe
        self._state_machine = state_machine
        self._paths = paths
        self._cancel_flag = cancel_flag
        self._failure_log = failure_log
        self._phase_healer = phase_healer
        self._save_lock = threading.Lock()
        self._transcode_pool_workers = max(
            1,
            transcode_pool_workers
            if transcode_pool_workers is not None
            else scheduler.backend_count(),
        )

    def run(self, job_id: str) -> JobSnapshot:
        """Download pending tracks and overlap transcode for ready media."""
        job = self._job_store.get(job_id)
        if job is None:
            raise InvalidJobError("job not found")
        if self._cancel_flag.is_cancelled():
            return job
        job = self._persist(self._phase_healer.heal(job), PipelineStage.MEDIA)
        ready = self._transcode_pending(job)
        download_pending = self._download_pending(job)
        if len(ready) == 0 and len(download_pending) == 0:
            return job
        if len(download_pending) > 0:
            job = self._mark_phases(
                job,
                download_pending,
                TrackPhase.DOWNLOADING,
                PipelineStage.MEDIA,
            )
        futures: list[Future[TranscodeResult]] = []
        with ThreadPoolExecutor(max_workers=self._transcode_pool_workers) as pool:
            for track in ready:
                if self._cancel_flag.is_cancelled():
                    break
                futures.append(self._submit_transcode(pool, job, track))
            if not self._cancel_flag.is_cancelled():
                for result in self._download_pool.iter_results(job, download_pending):
                    job = self._apply_download(job, result)
                    if self._cancel_flag.is_cancelled():
                        break
                    if not result.success:
                        continue
                    track = self._track_by_id(job, result.track_id)
                    if track is None:
                        continue
                    futures.append(self._submit_transcode(pool, job, track))
            job = self._drain_transcodes(job, futures)
        return job

    def _submit_transcode(
        self,
        pool: ThreadPoolExecutor,
        job: JobSnapshot,
        track: TrackRef,
    ) -> Future[TranscodeResult]:
        return pool.submit(self._transcode_when_slot_ready, job.job_id, track)

    def _transcode_when_slot_ready(
        self,
        job_id: str,
        track: TrackRef,
    ) -> TranscodeResult:
        with self._save_lock:
            latest = self._job_store.get(job_id)
            if latest is None:
                return TranscodeResult(
                    track_id=track.track_id,
                    success=False,
                    output_path=None,
                    backend=None,
                    error_message="job not found",
                )
            if self._cancel_flag.is_cancelled():
                return TranscodeResult(
                    track_id=track.track_id,
                    success=False,
                    output_path=None,
                    backend=None,
                    error_message="cancelled",
                )
            marked = self._mark_one_phase(
                latest,
                track.track_id,
                TrackPhase.TRANSCODING,
                PipelineStage.MEDIA,
            )
            self._job_store.save(marked)
        return self._scheduler.transcode_track(marked, track)

    def _drain_transcodes(
        self,
        job: JobSnapshot,
        futures: list[Future[TranscodeResult]],
    ) -> JobSnapshot:
        pending: set[Future[TranscodeResult]] = set(futures)
        while pending:
            done, pending = wait(pending, return_when=FIRST_COMPLETED)
            for future in done:
                job = self._apply_transcode(job, future.result())
        return self._persist(job, PipelineStage.MEDIA)

    def _apply_download(
        self,
        job: JobSnapshot,
        result: DownloadResult,
    ) -> JobSnapshot:
        with self._save_lock:
            latest = self._job_store.get(job.job_id) or job
            tracks = [
                self._download_track_update(latest, track, result)
                for track in latest.tracks
            ]
            saved = self._job_store.save(
                replace(
                    latest,
                    status=self._status(),
                    pipeline_stage=PipelineStage.MEDIA,
                    tracks=tracks,
                )
            )
        self._log_failure(saved, result.track_id)
        return saved

    def _apply_transcode(
        self,
        job: JobSnapshot,
        result: TranscodeResult,
    ) -> JobSnapshot:
        with self._save_lock:
            latest = self._job_store.get(job.job_id) or job
            tracks = [
                self._transcode_track_update(track, result)
                for track in latest.tracks
            ]
            saved = self._job_store.save(
                replace(
                    latest,
                    status=self._status(),
                    pipeline_stage=PipelineStage.MEDIA,
                    tracks=tracks,
                )
            )
        self._log_failure(saved, result.track_id)
        return saved

    def _log_failure(self, job: JobSnapshot, track_id: str) -> None:
        for track in job.tracks:
            if track.track_id != track_id:
                continue
            if track.phase is TrackPhase.ERROR and track.error_message:
                self._failure_log.append(job, track, track.error_message)
            return

    def _download_track_update(
        self,
        job: JobSnapshot,
        track: TrackRef,
        result: DownloadResult,
    ) -> TrackRef:
        if track.track_id != result.track_id:
            return track
        if result.success:
            marker = self._paths.download_complete_marker(job, track)
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text("ok", encoding="utf-8")
            return replace(track, phase=TrackPhase.DOWNLOADED, error_message=None)
        return replace(
            track,
            phase=TrackPhase.ERROR,
            error_message=result.error_message,
        )

    def _transcode_track_update(
        self,
        track: TrackRef,
        result: TranscodeResult,
    ) -> TrackRef:
        if track.track_id != result.track_id:
            return track
        if result.success:
            return replace(track, phase=TrackPhase.DONE, error_message=None)
        return replace(
            track,
            phase=TrackPhase.ERROR,
            error_message=result.error_message,
        )

    def _download_pending(self, job: JobSnapshot) -> list[TrackRef]:
        pending: list[TrackRef] = []
        for track in job.tracks:
            flags = self._artifact_probe.flags_for(job, track)
            if self._state_machine.decide(track, flags) is ResumeAction.DOWNLOAD:
                pending.append(track)
        return pending

    def _transcode_pending(self, job: JobSnapshot) -> list[TrackRef]:
        pending: list[TrackRef] = []
        for track in job.tracks:
            flags = self._artifact_probe.flags_for(job, track)
            if self._state_machine.decide(track, flags) is ResumeAction.TRANSCODE:
                pending.append(track)
        return pending

    def _mark_phases(
        self,
        job: JobSnapshot,
        tracks: list[TrackRef],
        phase: TrackPhase,
        stage: PipelineStage,
    ) -> JobSnapshot:
        ids = {track.track_id for track in tracks}
        updated = [
            replace(track, phase=phase, error_message=None)
            if track.track_id in ids
            else track
            for track in job.tracks
        ]
        return self._persist(replace(job, tracks=updated), stage)

    def _mark_one_phase(
        self,
        job: JobSnapshot,
        track_id: str,
        phase: TrackPhase,
        stage: PipelineStage,
    ) -> JobSnapshot:
        tracks = [
            replace(track, phase=phase, error_message=None)
            if track.track_id == track_id
            else track
            for track in job.tracks
        ]
        return replace(
            job,
            status=self._status(),
            pipeline_stage=stage,
            tracks=tracks,
        )

    def _persist(self, job: JobSnapshot, stage: PipelineStage) -> JobSnapshot:
        with self._save_lock:
            return self._job_store.save(
                replace(job, status=self._status(), pipeline_stage=stage)
            )

    def _status(self) -> JobStatus:
        if self._cancel_flag.is_cancelled():
            return JobStatus.CANCELLED
        return JobStatus.RUNNING

    def _track_by_id(self, job: JobSnapshot, track_id: str) -> TrackRef | None:
        for track in job.tracks:
            if track.track_id == track_id:
                return track
        return None
