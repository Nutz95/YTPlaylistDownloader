import httpx

from ytpd.domain.lm_studio_chat_message_payload import LmStudioChatMessagePayload
from ytpd.domain.lm_studio_chat_response import LmStudioChatResponse
from ytpd.domain.lm_studio_models_response import LmStudioModelsResponse
from ytpd.domain.lm_studio_response_format_payload import LmStudioResponseFormatPayload
from ytpd.lmstudio.lm_studio_chat_message_text import LmStudioChatMessageText
from ytpd.lmstudio.lm_studio_error import LmStudioError
from ytpd.lmstudio.lm_studio_settings import LmStudioSettings

_OFFLINE_MESSAGE = "LM Studio est hors ligne ou injoignable."
# Thinking models often burn most of a small budget on reasoning before JSON.
_MAX_COMPLETION_TOKENS = 512
# Top-level fields (not extra_body): LM Studio / llama.cpp read these on raw HTTP.
_REASONING_EFFORT = "none"
_CHAT_TEMPLATE_KWARGS: dict[str, bool] = {"enable_thinking": False}


class HttpxLmStudioHttpTransport:
    """httpx transport for LM Studio OpenAI-compatible HTTP APIs."""

    def __init__(self, settings: LmStudioSettings) -> None:
        self._settings = settings
        self._client = self._new_client()
        self._message_text = LmStudioChatMessageText()

    def get_models(self) -> LmStudioModelsResponse:
        """GET ``models`` and return reported model ids."""
        try:
            response = self._client.get("models")
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as error:
            raise LmStudioError(_OFFLINE_MESSAGE) from error
        except ValueError as error:
            raise LmStudioError("réponse LM Studio /models invalide") from error
        if not isinstance(payload, dict):
            raise LmStudioError("réponse LM Studio /models invalide")
        raw_data = payload.get("data")
        if not isinstance(raw_data, list):
            raise LmStudioError("réponse LM Studio /models invalide")
        ids: list[str] = []
        for item in raw_data:
            if isinstance(item, dict):
                model_id = item.get("id")
                if isinstance(model_id, str):
                    ids.append(model_id)
        return LmStudioModelsResponse(model_ids=ids)

    def post_chat(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        response_format: LmStudioResponseFormatPayload,
    ) -> LmStudioChatResponse:
        """POST ``chat/completions`` with LM Studio structured outputs."""
        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0,
            "response_format": response_format,
            "max_tokens": _MAX_COMPLETION_TOKENS,
            "reasoning_effort": _REASONING_EFFORT,
            "chat_template_kwargs": _CHAT_TEMPLATE_KWARGS,
        }
        try:
            response = self._client.post("chat/completions", json=body)
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as error:
            raise LmStudioError(_OFFLINE_MESSAGE) from error
        except ValueError as error:
            raise LmStudioError("réponse chat LM Studio invalide") from error
        if not isinstance(payload, dict):
            raise LmStudioError("réponse chat LM Studio invalide")
        choices = payload.get("choices")
        if not isinstance(choices, list) or len(choices) == 0:
            raise LmStudioError("réponse chat LM Studio sans choix")
        first = choices[0]
        if not isinstance(first, dict):
            raise LmStudioError("réponse chat LM Studio invalide")
        message = first.get("message")
        if not isinstance(message, dict):
            raise LmStudioError("réponse chat LM Studio invalide")
        finish_raw = first.get("finish_reason")
        finish_reason = finish_raw if isinstance(finish_raw, str) else None
        raw_content = message.get("content")
        raw_reasoning_content = message.get("reasoning_content")
        raw_reasoning = message.get("reasoning")
        typed_message: LmStudioChatMessagePayload = {
            "content": raw_content if isinstance(raw_content, str) else None,
            "reasoning_content": (
                raw_reasoning_content if isinstance(raw_reasoning_content, str) else None
            ),
            "reasoning": raw_reasoning if isinstance(raw_reasoning, str) else None,
        }
        content = self._message_text.extract(typed_message, finish_reason)
        return LmStudioChatResponse(content=content)

    def abort(self) -> None:
        """Close the HTTP client to unblock in-flight chat calls, then recreate it."""
        self._client.close()
        self._client = self._new_client()

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def _new_client(self) -> httpx.Client:
        return httpx.Client(
            base_url=self._settings.base_url.rstrip("/") + "/",
            timeout=self._settings.timeout_sec,
        )
