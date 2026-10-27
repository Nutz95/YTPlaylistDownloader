from typing import NotRequired, TypedDict


class LmStudioChatMessagePayload(TypedDict):
    """Subset of an LM Studio assistant message used for text extraction."""

    content: NotRequired[str | None]
    reasoning_content: NotRequired[str | None]
    reasoning: NotRequired[str | None]
