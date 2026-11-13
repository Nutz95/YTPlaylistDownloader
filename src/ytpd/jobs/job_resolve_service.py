from dataclasses import replace

from ytpd.domain.job_media_mode import JobMediaMode
from ytpd.domain.job_media_mode_policy import JobMediaModePolicy
from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.job_status import JobStatus
from ytpd.domain.pipeline_stage import PipelineStage
from ytpd.domain.track_ref import TrackRef
from ytpd.jobs.invalid_job_error import InvalidJobError
from ytpd.jobs.job_store import JobStore
from ytpd.jobs.video_chapter_collapser import VideoChapterCollapser
from ytpd.ports.playlist_resolver import PlaylistResolver
from ytpd.resolve.playlist_resolve_error import PlaylistResolveError


class JobResolveService:
    """Persist playlist resolve results onto a job exactly once."""

    def __init__(
        self,
        job_store: JobStore,
        playlist_resolver: PlaylistResolver,
        video_chapter_collapser: VideoChapterCollapser,
    ) -> None:
        self._job_store = job_store
        self._playlist_resolver = playlist_resolver
        self._video_chapter_collapser = video_chapter_collapser

    def resolve_job(self, job_id: str) -> JobSnapshot:
        """Resolve playlist metadata for ``job_id`` without re-fetch when tracks exist."""
        job = self._job_store.get(job_id)
        if job is None:
            raise InvalidJobError("job not found")
        if len(job.tracks) > 0:
            return job
        job = self._job_store.save(
            replace(
                job,
                status=JobStatus.RUNNING,
                pipeline_stage=PipelineStage.RESOLVE,
                error_message=None,
            )
        )
        try:
            resolved = self._playlist_resolver.resolve(job.source_url)
        except PlaylistResolveError as error:
            raise InvalidJobError(str(error)) from error
        tracks = self._tracks_for_mode(job.media_mode, resolved.tracks, resolved.source_title)
        updated = replace(
            job,
            source_kind=resolved.source_kind,
            status=JobStatus.RUNNING,
            pipeline_stage=PipelineStage.RESOLVE,
            tracks=tracks,
            source_title=resolved.source_title,
        )
        return self._job_store.save(updated)

    def _tracks_for_mode(
        self,
        media_mode: JobMediaMode,
        tracks: list[TrackRef],
        source_title: str | None,
    ) -> list[TrackRef]:
        policy = JobMediaModePolicy.for_mode(media_mode)
        if policy.collapse_chapters:
            return self._video_chapter_collapser.collapse(tracks, source_title)
        return tracks
