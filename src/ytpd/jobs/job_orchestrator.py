from dataclasses import replace

from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.job_status import JobStatus
from ytpd.domain.orchestrator_result import OrchestratorResult
from ytpd.domain.pipeline_stage import PipelineStage
from ytpd.domain.track_phase import TrackPhase
from ytpd.domain.track_ref import TrackRef
from ytpd.jobs.invalid_job_error import InvalidJobError
from ytpd.jobs.job_cancel_flag import JobCancelFlag
from ytpd.jobs.job_download_transcode_coordinator import (
    JobDownloadTranscodeCoordinator,
)
from ytpd.jobs.job_match_service import JobMatchService
from ytpd.jobs.job_resolve_service import JobResolveService
from ytpd.jobs.job_store import JobStore
from ytpd.ports.lm_studio_model_runtime import LmStudioModelRuntime
from ytpd.ports.output_catalog import OutputCatalog
from ytpd.ports.track_artifact_probe import TrackArtifactProbe


class JobOrchestrator:
    """Run resolve → match → overlapped download/transcode with cancel."""

    def __init__(
        self,
        job_store: JobStore,
        resolve_service: JobResolveService,
        match_service: JobMatchService,
        media_coordinator: JobDownloadTranscodeCoordinator,
        artifact_probe: TrackArtifactProbe,
        catalog: OutputCatalog,
        cancel_flag: JobCancelFlag,
        lm_runtime: LmStudioModelRuntime,
    ) -> None:
        self._job_store = job_store
        self._resolve_service = resolve_service
        self._match_service = match_service
        self._media_coordinator = media_coordinator
        self._artifact_probe = artifact_probe
        self._catalog = catalog
        self._cancel_flag = cancel_flag
        self._lm_runtime = lm_runtime

    def run_job(self, job_id: str) -> OrchestratorResult:
        """Execute the full pipeline for ``job_id`` until done or cancelled."""
        self._cancel_flag.clear()
        job = self._job_store.get(job_id)
        if job is None:
            raise InvalidJobError("job not found")
        job = self._job_store.save(
            replace(
                job,
                status=JobStatus.RUNNING,
                pipeline_stage=PipelineStage.RESOLVE,
                error_message=None,
            )
        )
        if len(job.tracks) == 0:
            job = self._resolve_service.resolve_job(job_id)
            job = self._job_store.save(
                replace(job, pipeline_stage=PipelineStage.RESOLVE, status=JobStatus.RUNNING)
            )
        if self._cancel_flag.is_cancelled():
            return self._cancelled(job)
        job = self._skip_catalogued(job)
        job = self._match_service.match_job(job.job_id)
        if self._cancel_flag.is_cancelled():
            return self._cancelled(job)
        self._lm_runtime.release()
        job = self._media_coordinator.run(job.job_id)
        if self._cancel_flag.is_cancelled():
            return self._cancelled(job)
        finished = replace(
            job,
            status=JobStatus.COMPLETED,
            pipeline_stage=None,
            error_message=None,
        )
        return OrchestratorResult(
            snapshot=self._job_store.save(finished),
            cancelled=False,
        )

    def cancel(self) -> None:
        """Request cooperative cancellation of the active run."""
        self._cancel_flag.cancel()

    def _skip_catalogued(self, job: JobSnapshot) -> JobSnapshot:
        known = {entry.track_id for entry in self._catalog.list_entries()}
        tracks: list[TrackRef] = []
        changed = False
        for track in job.tracks:
            flags = self._artifact_probe.flags_for(job, track)
            already = track.track_id in known or flags.mp3_present
            terminal = track.phase in {TrackPhase.SKIPPED, TrackPhase.DONE}
            if already and not terminal:
                tracks.append(
                    replace(track, phase=TrackPhase.SKIPPED, error_message=None)
                )
                changed = True
            else:
                tracks.append(track)
        if not changed:
            return job
        return self._job_store.save(replace(job, tracks=tracks))

    def _cancelled(self, job: JobSnapshot) -> OrchestratorResult:
        """Return a cancelled result; status freeze is owned by JobCancelFinalizer."""
        latest = self._job_store.get(job.job_id)
        snapshot = latest if latest is not None else job
        return OrchestratorResult(snapshot=snapshot, cancelled=True)
