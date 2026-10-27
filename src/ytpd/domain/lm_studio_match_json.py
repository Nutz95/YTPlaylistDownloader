from typing import TypedDict


class LmStudioMatchJson(TypedDict):
    """Structured JSON template returned by the LM Studio match prompt."""

    candidate_index: int | None
    reason: str
