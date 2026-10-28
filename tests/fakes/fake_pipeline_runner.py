from ytpd.domain.job_snapshot import JobSnapshot


class FakePipelineRunner:
    """Record cancel and drain calls for lifespan tests."""

    def __init__(self) -> None:
        self.cancel_calls = 0
        self.drain_calls = 0

    def drain_queue(self) -> JobSnapshot | None:
        """Record a startup drain request and return no snapshot."""
        self.drain_calls += 1
        return None

    def cancel(self, job_id: str | None = None) -> JobSnapshot | None:
        """Record a cancel request and return no snapshot."""
        self.cancel_calls += 1
        return None
