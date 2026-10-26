from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.track_artifact_flags import TrackArtifactFlags
from ytpd.domain.track_ref import TrackRef
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths


class PathTrackArtifactProbe:
    """Probe download/MP3 artefacts using ``TrackArtifactPaths``."""

    def __init__(self, paths: TrackArtifactPaths) -> None:
        self._paths = paths

    def flags_for(self, job: JobSnapshot, track: TrackRef) -> TrackArtifactFlags:
        """Return whether the download marker and destination MP3 exist."""
        return TrackArtifactFlags(
            download_complete=self._paths.download_complete_marker(job, track).is_file(),
            mp3_present=self._paths.destination_mp3(track).is_file(),
        )
