from dataclasses import dataclass


@dataclass(frozen=True)
class LmStudioChatResponse:
    """Assistant message text from an LM Studio chat completion."""

    content: str
