from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.track_artifact_flags import TrackArtifactFlags
from ytpd.domain.track_ref import TrackRef


class FakeTrackArtifactProbe:
    """In-memory artefact flags keyed by track id for resume unit tests."""

    def __init__(self, flags_by_track_id: dict[str, TrackArtifactFlags]) -> None:
        self._flags_by_track_id = dict(flags_by_track_id)

    def flags_for(self, job: JobSnapshot, track: TrackRef) -> TrackArtifactFlags:
        """Return configured flags; raise when the track id was not set up."""
        del job
        return self._flags_by_track_id[track.track_id]
