from dataclasses import replace

from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.job_status import JobStatus
from ytpd.domain.match_result import MatchResult
from ytpd.domain.pipeline_stage import PipelineStage
from ytpd.domain.track_phase import TrackPhase
from ytpd.domain.track_ref import TrackRef
from ytpd.jobs.invalid_job_error import InvalidJobError
from ytpd.jobs.job_cancel_flag import JobCancelFlag
from ytpd.jobs.job_failure_log import JobFailureLog
from ytpd.jobs.job_store import JobStore
from ytpd.match.match_pool import MatchPool
from ytpd.match.persisted_match_candidate_mapper import PersistedMatchCandidateMapper


class JobMatchService:
    """Run parallel YouTube matching for unresolved tracks and persist results."""

    def __init__(
        self,
        job_store: JobStore,
        match_pool: MatchPool,
        cancel_flag: JobCancelFlag,
        failure_log: JobFailureLog,
        candidate_mapper: PersistedMatchCandidateMapper | None = None,
    ) -> None:
        self._job_store = job_store
        self._match_pool = match_pool
        self._cancel_flag = cancel_flag
        self._failure_log = failure_log
        self._candidate_mapper = candidate_mapper or PersistedMatchCandidateMapper()

    def match_job(self, job_id: str) -> JobSnapshot:
        """Match pending tracks for ``job_id`` and save updated track phases."""
        job = self._job_store.get(job_id)
        if job is None:
            raise InvalidJobError("job not found")
        if len(job.tracks) == 0:
            raise InvalidJobError("job has no tracks to match")
        if self._cancel_flag.is_cancelled():
            return job
        job = self._mark_matching(job)
        pending = [track for track in job.tracks if track.phase is TrackPhase.MATCHING]
        if len(pending) == 0:
            return job
        for result in self._match_pool.iter_results(list(job.tracks)):
            job = self._apply_and_save(job, result)
            if self._cancel_flag.is_cancelled():
                break
        return job

    def _mark_matching(self, job: JobSnapshot) -> JobSnapshot:
        tracks = [
            replace(track, phase=TrackPhase.MATCHING, error_message=None)
            if track.needs_youtube_match()
            else track
            for track in job.tracks
        ]
        return self._job_store.save(
            replace(
                job,
                status=self._status_for_save(),
                pipeline_stage=PipelineStage.MATCH,
                tracks=tracks,
            )
        )

    def _apply_and_save(self, job: JobSnapshot, result: MatchResult) -> JobSnapshot:
        updated_tracks = [
            self._apply_result(track, result if track.track_id == result.track_id else None)
            for track in job.tracks
        ]
        saved = self._job_store.save(
            replace(
                job,
                status=self._status_for_save(),
                pipeline_stage=PipelineStage.MATCH,
                tracks=updated_tracks,
            )
        )
        for track in saved.tracks:
            if track.track_id != result.track_id:
                continue
            if track.phase is TrackPhase.MATCH_FAILED and track.error_message:
                self._failure_log.append(saved, track, track.error_message)
        return saved

    def _status_for_save(self) -> JobStatus:
        if self._cancel_flag.is_cancelled():
            return JobStatus.CANCELLED
        return JobStatus.RUNNING

    def _apply_result(
        self,
        track: TrackRef,
        result: MatchResult | None,
    ) -> TrackRef:
        if result is None:
            return track
        if result.matched and result.candidate is not None:
            return replace(
                track,
                phase=TrackPhase.MATCHED,
                youtube_url=result.candidate.youtube_url,
                error_message=None,
                match_candidates=[],
            )
        return replace(
            track,
            phase=TrackPhase.MATCH_FAILED,
            error_message=result.error_message,
            match_candidates=self._candidate_mapper.from_scored(result.candidates),
        )
