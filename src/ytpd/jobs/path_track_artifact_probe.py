from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.track_artifact_flags import TrackArtifactFlags
from ytpd.domain.track_ref import TrackRef
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths


class PathTrackArtifactProbe:
    """Probe download/MP3 artefacts using ``TrackArtifactPaths``."""

    def __init__(self, paths: TrackArtifactPaths) -> None:
        self._paths = paths

    def flags_for(self, job: JobSnapshot, track: TrackRef) -> TrackArtifactFlags:
        """Return whether the download media+marker and destination MP3 exist."""
        media = self._paths.download_media_file(job, track)
        marker = self._paths.download_complete_marker(job, track)
        download_complete = (
            marker.is_file() and media.is_file() and media.stat().st_size > 0
        )
        return TrackArtifactFlags(
            download_complete=download_complete,
            mp3_present=self._paths.destination_mp3(track).is_file(),
        )
