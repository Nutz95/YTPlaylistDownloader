from typing import Protocol


class ResourceGate(Protocol):
    """Exclusive access between LLM matching and GPU transcode work."""

    def acquire_llm(self) -> None:
        """Block until LLM may run (no GPU holders)."""

    def release_llm(self) -> None:
        """Release the LLM slot."""

    def try_acquire_gpu(self) -> bool:
        """Try to take a GPU slot; false while LLM is held."""

    def release_gpu(self) -> None:
        """Release one GPU slot."""
