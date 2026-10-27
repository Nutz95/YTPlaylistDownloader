class FakeLmStudioModelRuntime:
    """No-op LM Studio model runtime for offline unit tests."""

    def __init__(self, events: list[str] | None = None) -> None:
        self.ensure_ready_calls = 0
        self.release_calls = 0
        self.events = events if events is not None else []

    def ensure_ready(self) -> None:
        """Record that readiness was requested."""
        self.ensure_ready_calls += 1
        self.events.append("ensure_ready")

    def release(self) -> None:
        """Record that the model was released after matching."""
        self.release_calls += 1
        self.events.append("release")
