from typing import Protocol

from ytpd.domain.lm_studio_chat_response import LmStudioChatResponse
from ytpd.domain.lm_studio_models_response import LmStudioModelsResponse


class LmStudioHttpTransport(Protocol):
    """HTTP boundary for LM Studio OpenAI-compatible endpoints."""

    def get_models(self) -> LmStudioModelsResponse:
        """GET ``/models`` and return the parsed body."""

    def post_chat(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
    ) -> LmStudioChatResponse:
        """POST a single-turn chat completion and return the assistant text."""
