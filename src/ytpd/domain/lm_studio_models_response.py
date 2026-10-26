from dataclasses import dataclass


@dataclass(frozen=True)
class LmStudioModelsResponse:
    """Model ids reported by LM Studio ``/models``."""

    model_ids: tuple[str, ...]
