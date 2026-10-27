class FakeProcessKiller:
    """Record kill requests without touching the OS."""

    def __init__(self) -> None:
        self.killed_pids: list[int] = []

    def kill(self, pid: int) -> None:
        """Record ``pid`` as terminated."""
        self.killed_pids.append(pid)
