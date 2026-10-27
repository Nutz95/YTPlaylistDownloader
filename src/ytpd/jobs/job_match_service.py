from dataclasses import replace

from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.job_status import JobStatus
from ytpd.domain.match_result import MatchResult
from ytpd.domain.track_phase import TrackPhase
from ytpd.domain.track_ref import TrackRef
from ytpd.jobs.invalid_job_error import InvalidJobError
from ytpd.jobs.job_store import JobStore
from ytpd.match.match_pool import MatchPool


class JobMatchService:
    """Run parallel YouTube matching for unresolved tracks and persist results."""

    def __init__(self, job_store: JobStore, match_pool: MatchPool) -> None:
        self._job_store = job_store
        self._match_pool = match_pool

    def match_job(self, job_id: str) -> JobSnapshot:
        """Match pending tracks for ``job_id`` and save updated track phases."""
        job = self._job_store.get(job_id)
        if job is None:
            raise InvalidJobError("job not found")
        if len(job.tracks) == 0:
            raise InvalidJobError("job has no tracks to match")
        results = self._match_pool.run(list(job.tracks))
        if len(results) == 0:
            return job
        by_id = {item.track_id: item for item in results}
        updated_tracks = [
            self._apply_result(track, by_id.get(track.track_id)) for track in job.tracks
        ]
        updated = replace(
            job,
            status=JobStatus.RUNNING,
            tracks=updated_tracks,
        )
        return self._job_store.save(updated)

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
            )
        return replace(
            track,
            phase=TrackPhase.MATCH_FAILED,
            error_message=result.error_message,
        )
