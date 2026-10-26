from dataclasses import dataclass


@dataclass(frozen=True)
class LmStudioSettings:
    """Connection settings for a local LM Studio OpenAI-compatible server."""

    base_url: str
    model: str
    timeout_sec: float
