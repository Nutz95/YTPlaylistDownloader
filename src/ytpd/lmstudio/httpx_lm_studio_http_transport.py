import httpx

from ytpd.domain.lm_studio_chat_response import LmStudioChatResponse
from ytpd.domain.lm_studio_models_response import LmStudioModelsResponse
from ytpd.lmstudio.lm_studio_error import LmStudioError
from ytpd.lmstudio.lm_studio_settings import LmStudioSettings

_OFFLINE_MESSAGE = "LM Studio est hors ligne ou injoignable."


class HttpxLmStudioHttpTransport:
    """httpx transport for LM Studio OpenAI-compatible HTTP APIs."""

    def __init__(self, settings: LmStudioSettings) -> None:
        self._settings = settings
        self._client = httpx.Client(
            base_url=settings.base_url.rstrip("/") + "/",
            timeout=settings.timeout_sec,
        )

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
    ) -> LmStudioChatResponse:
        """POST ``chat/completions`` and return the assistant content."""
        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0,
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
        content = message.get("content")
        if not isinstance(content, str) or content.strip() == "":
            raise LmStudioError("réponse chat LM Studio vide")
        return LmStudioChatResponse(content=content)

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()
