from typing import Protocol


class ProcessKiller(Protocol):
    """Terminate an OS process by pid."""

    def kill(self, pid: int) -> None:
        """Force-terminate ``pid`` (and its children when the platform allows)."""
