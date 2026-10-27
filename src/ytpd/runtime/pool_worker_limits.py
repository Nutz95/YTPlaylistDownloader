import os


class PoolWorkerLimits:
    """Compute match vs download thread-pool sizes for the composition root."""

    _MATCH_CAP = 8
    _DOWNLOAD_CAP = 2

    def match_workers(self) -> int:
        """Return match parallelism (capped, based on CPU count)."""
        return min(self._MATCH_CAP, os.cpu_count() or 4)

    def download_workers(self) -> int:
        """Return download parallelism (low to reduce YouTube 429 / bot checks)."""
        return self._DOWNLOAD_CAP
