from dataclasses import dataclass

from ytpd.domain.resume_action import ResumeAction


@dataclass(frozen=True)
class TrackResumeDecision:
    """Resume action chosen for one track."""

    track_id: str
    action: ResumeAction
