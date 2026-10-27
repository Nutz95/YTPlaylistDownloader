from ytpd.domain.lm_studio_chat_response import LmStudioChatResponse
from ytpd.domain.lm_studio_models_response import LmStudioModelsResponse
from ytpd.lmstudio.lm_studio_error import LmStudioError


class FakeLmStudioHttpTransport:
    """Configurable LM Studio HTTP double for offline tests."""

    def __init__(
        self,
        model_ids: list[str],
        chat_replies: list[str],
        offline: bool = False,
    ) -> None:
        self._model_ids = list(model_ids)
        self._chat_replies = list(chat_replies)
        self._offline = offline
        self.chat_calls = 0

    def get_models(self) -> LmStudioModelsResponse:
        """Return configured models or raise when offline."""
        if self._offline:
            raise LmStudioError("LM Studio est hors ligne ou injoignable.")
        return LmStudioModelsResponse(model_ids=self._model_ids)

    def post_chat(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
    ) -> LmStudioChatResponse:
        """Return the next scripted chat reply."""
        if self._offline:
            raise LmStudioError("LM Studio est hors ligne ou injoignable.")
        if len(self._chat_replies) == 0:
            raise LmStudioError("réponse chat LM Studio vide")
        self.chat_calls += 1
        return LmStudioChatResponse(content=self._chat_replies.pop(0))
