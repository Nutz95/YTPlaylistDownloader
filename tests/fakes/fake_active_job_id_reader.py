class FakeActiveJobIdReader:
    """Test double that reports a fixed active job id."""

    def __init__(self, job_id: str | None = None) -> None:
        self._job_id = job_id

    def active_job_id(self) -> str | None:
        """Return the configured active job id."""
        return self._job_id
