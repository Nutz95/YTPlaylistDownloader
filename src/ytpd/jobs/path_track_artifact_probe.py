from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.track_artifact_flags import TrackArtifactFlags
from ytpd.domain.track_ref import TrackRef
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths


class PathTrackArtifactProbe:
    """Probe download and destination artefacts using ``TrackArtifactPaths``."""

    def __init__(self, paths: TrackArtifactPaths) -> None:
        self._paths = paths

    def flags_for(self, job: JobSnapshot, track: TrackRef) -> TrackArtifactFlags:
        """Return whether the download media+marker and destination output exist."""
        media = self._paths.download_media_file(job, track)
        marker = self._paths.download_complete_marker(job, track)
        download_complete = (
            marker.is_file() and media.is_file() and media.stat().st_size > 0
        )
        destination = self._paths.destination_file(job, track)
        return TrackArtifactFlags(
            download_complete=download_complete,
            output_present=destination.is_file() and destination.stat().st_size > 0,
        )
