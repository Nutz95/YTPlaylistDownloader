import os


class CpuParallelism:
    """Resolve how many CPU transcode workers to run."""

    def worker_count(self) -> int:
        """Return ``os.cpu_count()`` with a minimum of 1."""
        return max(1, os.cpu_count() or 1)
