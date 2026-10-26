from dataclasses import replace

from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.job_status import JobStatus
from ytpd.jobs.invalid_job_error import InvalidJobError
from ytpd.jobs.job_store import JobStore
from ytpd.ports.playlist_resolver import PlaylistResolver
from ytpd.resolve.playlist_resolve_error import PlaylistResolveError


class JobResolveService:
    """Persist playlist resolve results onto a job exactly once."""

    def __init__(
        self,
        job_store: JobStore,
        playlist_resolver: PlaylistResolver,
    ) -> None:
        self._job_store = job_store
        self._playlist_resolver = playlist_resolver

    def resolve_job(self, job_id: str) -> JobSnapshot:
        """Resolve playlist metadata for ``job_id`` without re-fetch when tracks exist."""
        job = self._job_store.get(job_id)
        if job is None:
            raise InvalidJobError("job not found")
        if len(job.tracks) > 0:
            return job
        try:
            resolved = self._playlist_resolver.resolve(job.source_url)
        except PlaylistResolveError as error:
            raise InvalidJobError(str(error)) from error
        updated = replace(
            job,
            source_kind=resolved.source_kind,
            status=JobStatus.RUNNING,
            tracks=resolved.tracks,
        )
        return self._job_store.save(updated)
