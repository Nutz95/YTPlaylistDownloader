from ytpd.lmstudio.lm_studio_api_root import LmStudioApiRoot


def test_strips_trailing_v1() -> None:
    root = LmStudioApiRoot().from_openai_base_url("http://127.0.0.1:1234/v1")
    assert root == "http://127.0.0.1:1234"


def test_keeps_non_v1_base() -> None:
    root = LmStudioApiRoot().from_openai_base_url("http://127.0.0.1:1234")
    assert root == "http://127.0.0.1:1234"
