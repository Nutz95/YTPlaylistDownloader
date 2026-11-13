from pathlib import Path

from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.jobs.invalid_job_error import InvalidJobError
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths
from ytpd.ports.output_catalog import OutputCatalog


class JobForceReprocessCleaner:
    """Remove existing work/destination artefacts so a forced job runs again."""

    def __init__(self, paths: TrackArtifactPaths, catalog: OutputCatalog) -> None:
        self._paths = paths
        self._catalog = catalog

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
                if not self._unlink(path):
                    remaining.append(str(path))
            self._catalog.delete(track.track_id)
        if remaining:
            joined = ", ".join(remaining)
            raise InvalidJobError(
                f"force reprocess could not delete locked files: {joined}"
            )

    def _unlink(self, path: Path) -> bool:
        if not path.is_file():
            return True
        try:
            path.unlink()
        except OSError:
            return not path.is_file()
        return not path.is_file()
