from dataclasses import replace

from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.job_status import JobStatus
from ytpd.domain.track_phase import TrackPhase
from ytpd.jobs.invalid_job_error import InvalidJobError
from ytpd.jobs.job_store import JobStore
from ytpd.jobs.youtube_url_validator import YoutubeUrlValidator

_OVERRIDEABLE = frozenset({TrackPhase.MATCH_FAILED, TrackPhase.ERROR})


class JobTrackYoutubeOverrideService:
    """Force a YouTube URL on a failed track and mark it matched for retry."""

    def __init__(
        self,
        job_store: JobStore,
        url_validator: YoutubeUrlValidator | None = None,
    ) -> None:
        self._job_store = job_store
        self._url_validator = url_validator or YoutubeUrlValidator()

    def apply(
        self,
        job_id: str,
        track_id: str,
        youtube_url: str,
    ) -> JobSnapshot:
        """Set ``youtube_url`` on a failed track and persist ``MATCHED`` phase."""
        job = self._job_store.get(job_id)
        if job is None:
            raise InvalidJobError("job not found")
        if job.status is JobStatus.RUNNING:
            raise InvalidJobError("stop the running pipeline before overriding a track")
        normalized = self._url_validator.normalize(youtube_url)
        if normalized is None:
            raise InvalidJobError("youtube_url must be a YouTube watch or youtu.be link")
        found = False
        tracks = []
        for track in job.tracks:
            if track.track_id != track_id:
                tracks.append(track)
                continue
            if track.phase not in _OVERRIDEABLE:
                raise InvalidJobError("track is not in a failed state")
            found = True
            tracks.append(
                replace(
                    track,
                    youtube_url=normalized,
                    phase=TrackPhase.MATCHED,
                    error_message=None,
                    match_candidates=[],
                )
            )
        if not found:
            raise InvalidJobError("track not found")
        return self._job_store.save(
            replace(
                job,
                status=JobStatus.INTERRUPTED,
                pipeline_stage=None,
                error_message=None,
                tracks=tracks,
            )
        )
