from dataclasses import dataclass


@dataclass(frozen=True)
class LmStudioMatchChoice:
    """LLM selection among ranked YouTube candidates."""

    candidate_index: int | None
    error_message: str | None
