from ytpd.runtime.os_process_ref import OsProcessRef


class FakeProcessLister:
    """Return a fixed process list for sibling-guard unit tests."""

    def __init__(self, processes: list[OsProcessRef]) -> None:
        self._processes = list(processes)

    def list_processes(self) -> list[OsProcessRef]:
        """Return the configured processes."""
        return list(self._processes)
