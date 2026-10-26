import threading


class JobCancelFlag:
    """Thread-safe cooperative cancellation signal for one orchestrator run."""

    def __init__(self) -> None:
        self._event = threading.Event()

    def cancel(self) -> None:
        """Request cooperative cancellation."""
        self._event.set()

    def is_cancelled(self) -> bool:
        """Return true when cancellation was requested."""
        return self._event.is_set()

    def clear(self) -> None:
        """Clear a previous cancellation request."""
        self._event.clear()
