from ytpd.domain.lm_studio_response_format_payload import LmStudioResponseFormatPayload


class LmStudioMatchStructuredFormat:
    """Build the LM Studio structured-output ``response_format`` for match choice."""

    def response_format(self) -> LmStudioResponseFormatPayload:
        """Return the json_schema response_format for candidate_index + reason."""
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "youtube_match_choice",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "candidate_index": {"type": ["integer", "null"]},
                        "reason": {"type": "string"},
                    },
                    "required": ["candidate_index", "reason"],
                    "additionalProperties": False,
                },
            },
        }
