from dataclasses import dataclass

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

    def __post_init__(self) -> None:
        object.__setattr__(self, "tracks", list(self.tracks))
