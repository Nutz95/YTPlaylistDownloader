from typing import Protocol


class LmStudioModelLoader(Protocol):
    """Native LM Studio load / unload boundary."""

    def load_model(self) -> None:
        """Load the configured model into LM Studio."""

    def unload_model(self) -> None:
        """Unload the configured model from LM Studio."""
