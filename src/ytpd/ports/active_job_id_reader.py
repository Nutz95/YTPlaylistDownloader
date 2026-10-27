from typing import Protocol


class ActiveJobIdReader(Protocol):
    """Read which job id is currently running in the pipeline, if any."""

    def active_job_id(self) -> str | None:
        """Return the active job id, or None when idle."""
