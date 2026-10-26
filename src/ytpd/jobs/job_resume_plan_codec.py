from typing import cast

from ytpd.domain.job_resume_plan import JobResumePlan
from ytpd.web.job_resume_plan_json_payload import JobResumePlanJsonPayload
from ytpd.web.resume_action_name import ResumeActionName


class JobResumePlanCodec:
    """Convert resume plans to the API JSON contract."""

    def to_payload(self, plan: JobResumePlan) -> JobResumePlanJsonPayload:
        """Serialize a resume plan for HTTP responses."""
        return {
            "job_id": plan.job_id,
            "job_action": cast(ResumeActionName, plan.job_action.value),
            "decisions": [
                {
                    "track_id": item.track_id,
                    "action": cast(ResumeActionName, item.action.value),
                }
                for item in plan.decisions
            ],
        }
