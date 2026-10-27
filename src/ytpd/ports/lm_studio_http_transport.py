from typing import Protocol

from ytpd.domain.lm_studio_chat_response import LmStudioChatResponse
from ytpd.domain.lm_studio_models_response import LmStudioModelsResponse
from ytpd.domain.lm_studio_response_format_payload import LmStudioResponseFormatPayload


class LmStudioHttpTransport(Protocol):
    """HTTP boundary for LM Studio OpenAI-compatible endpoints."""

    def get_models(self) -> LmStudioModelsResponse:
        """GET ``/models`` and return the parsed body."""

    def post_chat(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        response_format: LmStudioResponseFormatPayload,
    ) -> LmStudioChatResponse:
        """POST a chat completion with structured-output response_format."""
