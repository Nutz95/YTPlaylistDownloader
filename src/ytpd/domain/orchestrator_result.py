from dataclasses import dataclass

from ytpd.domain.job_snapshot import JobSnapshot


@dataclass(frozen=True)
class OrchestratorResult:
    """Final job snapshot after a cooperative pipeline run."""

    snapshot: JobSnapshot
    cancelled: bool
