from typing import Protocol

from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.track_artifact_flags import TrackArtifactFlags
from ytpd.domain.track_ref import TrackRef


class TrackArtifactProbe(Protocol):
    """Probe download and destination artefacts for resume decisions."""

    def flags_for(self, job: JobSnapshot, track: TrackRef) -> TrackArtifactFlags:
        """Return presence flags for ``track`` inside ``job``."""
