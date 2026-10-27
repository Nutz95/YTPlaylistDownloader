from dataclasses import dataclass


@dataclass(frozen=True)
class GlobalProgress:
    """Aggregate progress for one job."""

    percent: float
    completed_tracks: int
    total_tracks: int
    label: str
    stage: str
    stage_done: int
    stage_total: int
