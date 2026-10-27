from ytpd.domain.job_snapshot import JobSnapshot


class FakePipelineRunner:
    """Record cancel calls for lifespan shutdown tests."""

    def __init__(self) -> None:
        self.cancel_calls = 0

    def cancel(self, job_id: str | None = None) -> JobSnapshot | None:
        """Record a cancel request and return no snapshot."""
        self.cancel_calls += 1
        return None
