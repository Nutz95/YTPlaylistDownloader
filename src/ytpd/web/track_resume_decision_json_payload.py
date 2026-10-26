from typing import TypedDict

from ytpd.web.resume_action_name import ResumeActionName


class TrackResumeDecisionJsonPayload(TypedDict):
    """JSON shape for one track resume decision."""

    track_id: str
    action: ResumeActionName
