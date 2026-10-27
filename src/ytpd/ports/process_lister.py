from typing import Protocol

from ytpd.runtime.os_process_ref import OsProcessRef


class ProcessLister(Protocol):
    """List running OS processes with command lines."""

    def list_processes(self) -> list[OsProcessRef]:
        """Return visible processes (best-effort; may omit access-denied rows)."""
