from dataclasses import dataclass

from ytpd.jobs.job_orchestrator_stack import JobOrchestratorStack
from ytpd.jobs.job_store import JobStore


@dataclass(frozen=True)
class PipelineRunnerTestStack:
    """Job store plus orchestrator stack for pipeline runner unit tests."""

    store: JobStore
    stack: JobOrchestratorStack
