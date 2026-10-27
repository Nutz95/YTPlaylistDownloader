class FakeCpuParallelism:
    """Fixed worker-count stand-in for ``CpuParallelism``."""

    def __init__(self, worker_count: int) -> None:
        self._worker_count = max(1, worker_count)

    def worker_count(self) -> int:
        """Return the configured worker count."""
        return self._worker_count
