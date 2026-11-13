from dataclasses import dataclass

from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.track_ref import TrackRef


@dataclass(frozen=True)
class ForceReprocessJobParts:
    """Job snapshot plus the single track used in force-reprocess unit tests."""

    job: JobSnapshot
    track: TrackRef
