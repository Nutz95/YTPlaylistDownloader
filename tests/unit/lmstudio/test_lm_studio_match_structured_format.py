from ytpd.lmstudio.lm_studio_match_structured_format import (
    LmStudioMatchStructuredFormat,
)


def test_structured_format_uses_json_schema() -> None:
    payload = LmStudioMatchStructuredFormat().response_format()
    assert payload["type"] == "json_schema"
    assert payload["json_schema"]["name"] == "youtube_match_choice"
    assert payload["json_schema"]["strict"] is True
    schema = payload["json_schema"]["schema"]
    assert schema["type"] == "object"
    assert schema["required"] == ["candidate_index", "reason"]
    assert schema["additionalProperties"] is False
    assert schema["properties"]["candidate_index"]["type"] == ["integer", "null"]
    assert schema["properties"]["reason"]["type"] == "string"
