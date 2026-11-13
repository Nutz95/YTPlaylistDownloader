from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.jobs.invalid_job_error import InvalidJobError
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths
from ytpd.ports.output_catalog import OutputCatalog
from ytpd.ports.path_unlinker import PathUnlinker


class JobForceReprocessCleaner:
    """Remove existing work/destination artefacts so a forced job runs again."""

    def __init__(
        self,
        paths: TrackArtifactPaths,
        catalog: OutputCatalog,
        unlinker: PathUnlinker,
    ) -> None:
        self._paths = paths
        self._catalog = catalog
        self._unlinker = unlinker

    def clear(self, job: JobSnapshot) -> None:
        """Delete download/destination files and catalogue rows for ``job``."""
        remaining: list[str] = []
        for track in job.tracks:
            for path in (
                self._paths.destination_file(job, track),
                self._paths.download_media_file(job, track),
                self._paths.download_partial_file(job, track),
                self._paths.download_complete_marker(job, track),
            ):
                if not self._unlinker.try_unlink(path):
                    remaining.append(str(path))
            self._catalog.delete(track.track_id)
        if remaining:
            joined = ", ".join(remaining)
            raise InvalidJobError(
                f"force reprocess could not delete locked files: {joined}"
            )
