import pytest

from ytpd.lmstudio.lm_studio_chat_message_text import LmStudioChatMessageText
from ytpd.lmstudio.lm_studio_error import LmStudioError


def test_prefers_content_over_reasoning() -> None:
    text = LmStudioChatMessageText().extract(
        {"content": '{"candidate_index": 1, "reason": "ok"}', "reasoning_content": "noise"},
        "stop",
    )
    assert "candidate_index" in text


def test_falls_back_to_reasoning_content_when_content_empty() -> None:
    text = LmStudioChatMessageText().extract(
        {
            "content": "",
            "reasoning_content": '{"candidate_index": 0, "reason": "from reasoning"}',
        },
        "stop",
    )
    assert text.startswith("{")


def test_empty_message_includes_finish_reason() -> None:
    with pytest.raises(LmStudioError, match="finish_reason=length"):
        LmStudioChatMessageText().extract({"content": ""}, "length")
