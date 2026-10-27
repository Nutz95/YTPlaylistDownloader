from typing import Protocol


class LmStudioModelRuntime(Protocol):
    """Ensure the configured LM Studio model is loaded before chat calls."""

    def ensure_ready(self) -> None:
        """Load (or reload) the model so chat completions can run."""

    def release(self) -> None:
        """Unload the model to free GPU memory after matching."""
