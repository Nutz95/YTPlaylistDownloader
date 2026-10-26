from dataclasses import dataclass

from ytpd.domain.track_phase import TrackPhase


@dataclass(frozen=True)
class MediaProgress:
    """Progress for one media currently downloading or transcoding."""

    track_id: str
    title: str
    phase: TrackPhase
    detail: str
