from typing import TypedDict

from ytpd.web.resume_action_name import ResumeActionName
from ytpd.web.track_resume_decision_json_payload import TrackResumeDecisionJsonPayload


class JobResumePlanJsonPayload(TypedDict):
    """JSON shape for a job resume plan."""

    job_id: str
    job_action: ResumeActionName
    decisions: list[TrackResumeDecisionJsonPayload]
