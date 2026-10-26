from dataclasses import dataclass

from ytpd.domain.resume_action import ResumeAction
from ytpd.domain.track_resume_decision import TrackResumeDecision


@dataclass(frozen=True)
class JobResumePlan:
    """Resume plan: one job-level action plus per-track decisions."""

    job_id: str
    job_action: ResumeAction
    decisions: list[TrackResumeDecision]

    def __post_init__(self) -> None:
        object.__setattr__(self, "decisions", list(self.decisions))

    def is_actionable(self) -> bool:
        """Return True when resolve or any track still needs pipeline work."""
        if self.job_action is not ResumeAction.NONE:
            return True
        return any(item.action is not ResumeAction.NONE for item in self.decisions)
