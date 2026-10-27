from typing import Literal, TypedDict


class LmStudioResponseFormatPayload(TypedDict):
    """``response_format`` body for LM Studio structured JSON outputs."""

    type: Literal["json_schema"]
    json_schema: dict[str, str | bool | dict[str, str | bool | list[str] | dict[str, str | list[str | None]]]]
