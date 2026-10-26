from dataclasses import dataclass


@dataclass(frozen=True)
class MediaProgress:
    """Progress for one media currently downloading or transcoding."""

    track_id: str
    title: str
    phase_label: str
    detail: str
