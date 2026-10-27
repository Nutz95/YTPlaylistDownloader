import pytest

from ytpd.lmstudio.lm_studio_error import LmStudioError
from ytpd.lmstudio.lm_studio_match_json_parser import LmStudioMatchJsonParser


def test_parse_valid_json_choice() -> None:
    result = LmStudioMatchJsonParser().parse(
        '{"candidate_index": 1, "reason": "title match"}',
        3,
    )
    assert result.candidate_index == 1
    assert result.error_message is None


def test_parse_null_index() -> None:
    result = LmStudioMatchJsonParser().parse(
        '{"candidate_index": null, "reason": "nope"}',
        2,
    )
    assert result.candidate_index is None
    assert result.error_message == "nope"


def test_parse_rejects_invalid_json() -> None:
    with pytest.raises(LmStudioError):
        LmStudioMatchJsonParser().parse("not-json", 1)


def test_parse_strips_think_blocks() -> None:
    result = LmStudioMatchJsonParser().parse(
        '<think>long reasoning</think>{"candidate_index": 0, "reason": "ok"}',
        2,
    )
    assert result.candidate_index == 0
    assert result.error_message is None
