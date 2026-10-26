from ytpd.domain.job_resume_plan import JobResumePlan
from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.resume_action import ResumeAction
from ytpd.domain.track_resume_decision import TrackResumeDecision
from ytpd.jobs.track_state_machine import TrackStateMachine
from ytpd.ports.track_artifact_probe import TrackArtifactProbe


class JobResumePlanner:
    """Pure planner: derive a resume plan from a job snapshot and artefacts."""

    def __init__(
        self,
        state_machine: TrackStateMachine,
        artifact_probe: TrackArtifactProbe,
    ) -> None:
        self._state_machine = state_machine
        self._artifact_probe = artifact_probe

    def plan(self, job: JobSnapshot) -> JobResumePlan:
        """Compute job-level and per-track resume actions without mutating state."""
        if len(job.tracks) == 0:
            return JobResumePlan(
                job_id=job.job_id,
                job_action=ResumeAction.RESOLVE_PLAYLIST,
                decisions=(),
            )
        decisions = tuple(
            TrackResumeDecision(
                track_id=track.track_id,
                action=self._state_machine.decide(
                    track,
                    self._artifact_probe.flags_for(job, track),
                ),
            )
            for track in job.tracks
        )
        return JobResumePlan(
            job_id=job.job_id,
            job_action=ResumeAction.NONE,
            decisions=decisions,
        )
