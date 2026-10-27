from ytpd.domain.lm_studio_chat_message_payload import LmStudioChatMessagePayload
from ytpd.lmstudio.lm_studio_error import LmStudioError


class LmStudioChatMessageText:
    """Extract usable assistant text from an LM Studio chat message object."""

    def extract(
        self,
        message: LmStudioChatMessagePayload,
        finish_reason: str | None,
    ) -> str:
        """Return content, falling back to reasoning fields when content is empty."""
        content = message.get("content")
        if isinstance(content, str) and content.strip() != "":
            return content
        reasoning_content = message.get("reasoning_content")
        if isinstance(reasoning_content, str) and reasoning_content.strip() != "":
            return reasoning_content
        reasoning = message.get("reasoning")
        if isinstance(reasoning, str) and reasoning.strip() != "":
            return reasoning
        reason = finish_reason or "unknown"
        raise LmStudioError(f"réponse chat LM Studio vide (finish_reason={reason})")
