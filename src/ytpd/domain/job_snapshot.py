from dataclasses import dataclass, replace

from ytpd.domain.job_status import JobStatus
from ytpd.domain.source_kind import SourceKind
from ytpd.domain.track_ref import TrackRef


@dataclass(frozen=True)
class JobSnapshot:
    """Immutable view of a job and its tracks at a point in time."""

    job_id: str
    source_url: str
    source_kind: SourceKind
    status: JobStatus
    tracks: list[TrackRef]
    error_message: str | None

    def with_status(self, status: JobStatus) -> "JobSnapshot":
        """Return a copy of this snapshot with a different lifecycle status."""
        return replace(self, status=status)
