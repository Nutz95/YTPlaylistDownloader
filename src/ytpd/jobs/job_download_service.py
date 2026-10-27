from dataclasses import replace

from ytpd.domain.download_result import DownloadResult
from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.job_status import JobStatus
from ytpd.domain.resume_action import ResumeAction
from ytpd.domain.track_phase import TrackPhase
from ytpd.domain.track_ref import TrackRef
from ytpd.download.download_pool import DownloadPool
from ytpd.jobs.invalid_job_error import InvalidJobError
from ytpd.jobs.job_store import JobStore
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths
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
    ) -> None:
        self._job_store = job_store
        self._download_pool = download_pool
        self._artifact_probe = artifact_probe
        self._state_machine = state_machine
        self._paths = paths

    def download_job(self, job_id: str) -> JobSnapshot:
        """Download pending matched tracks for ``job_id`` and save results."""
        job = self._job_store.get(job_id)
        if job is None:
            raise InvalidJobError("job not found")
        healed = self._heal_completed_phases(job)
        pending = self._pending_tracks(healed)
        if len(pending) == 0:
            if healed is job:
                return job
            return self._job_store.save(healed)
        results = self._download_pool.run(healed, pending)
        by_id = {item.track_id: item for item in results}
        updated_tracks = [
            self._apply_result(healed, track, by_id.get(track.track_id))
            for track in healed.tracks
        ]
        return self._job_store.save(
            replace(healed, status=JobStatus.RUNNING, tracks=updated_tracks)
        )

    def _heal_completed_phases(self, job: JobSnapshot) -> JobSnapshot:
        changed = False
        tracks: list[TrackRef] = []
        for track in job.tracks:
            flags = self._artifact_probe.flags_for(job, track)
            if (
                flags.download_complete
                and track.phase is not TrackPhase.DOWNLOADED
                and track.phase not in {TrackPhase.SKIPPED, TrackPhase.DONE}
                and track.phase is not TrackPhase.TRANSCODING
            ):
                tracks.append(replace(track, phase=TrackPhase.DOWNLOADED, error_message=None))
                changed = True
            else:
                tracks.append(track)
        if not changed:
            return job
        return replace(job, tracks=tracks)

    def _pending_tracks(self, job: JobSnapshot) -> list[TrackRef]:
        pending: list[TrackRef] = []
        for track in job.tracks:
            flags = self._artifact_probe.flags_for(job, track)
            action = self._state_machine.decide(track, flags)
            if action is ResumeAction.DOWNLOAD:
                pending.append(track)
        return pending

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
