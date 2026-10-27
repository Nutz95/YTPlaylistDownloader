import json
import re

from ytpd.domain.lm_studio_match_choice import LmStudioMatchChoice
from ytpd.domain.lm_studio_match_json import LmStudioMatchJson
from ytpd.lmstudio.lm_studio_error import LmStudioError

_THINK_BLOCK = re.compile(r"<think>[\s\S]*?</think>", re.IGNORECASE)
_THINK_UNCLOSED = re.compile(r"<think>[\s\S]*$", re.IGNORECASE)


class LmStudioMatchJsonParser:
    """Parse a forced JSON LM Studio reply into ``LmStudioMatchChoice``."""

    def parse(self, content: str, candidate_count: int) -> LmStudioMatchChoice:
        """Decode JSON and validate the candidate index bounds."""
        try:
            loaded = json.loads(self._extract_json_object(content))
        except json.JSONDecodeError as error:
            raise LmStudioError("réponse LLM JSON invalide") from error
        if not isinstance(loaded, dict):
            raise LmStudioError("réponse LLM JSON invalide")
        index_raw = loaded.get("candidate_index")
        reason_raw = loaded.get("reason", "")
        if index_raw is not None and (
            isinstance(index_raw, bool) or not isinstance(index_raw, int)
        ):
            raise LmStudioError("candidate_index LLM invalide")
        if not isinstance(reason_raw, str):
            raise LmStudioError("reason LLM invalide")
        payload: LmStudioMatchJson = {
            "candidate_index": index_raw,
            "reason": reason_raw,
        }
        if payload["candidate_index"] is None:
            return LmStudioMatchChoice(
                candidate_index=None,
                error_message=payload["reason"] or "LLM: aucun candidat retenu",
            )
        index = payload["candidate_index"]
        if index < 0 or index >= candidate_count:
            return LmStudioMatchChoice(
                candidate_index=None,
                error_message="index LLM hors bornes",
            )
        return LmStudioMatchChoice(candidate_index=index, error_message=None)

    def _extract_json_object(self, content: str) -> str:
        cleaned = _THINK_BLOCK.sub("", content)
        cleaned = _THINK_UNCLOSED.sub("", cleaned).strip()
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start < 0 or end <= start:
            raise LmStudioError("réponse LLM JSON introuvable")
        return cleaned[start : end + 1]
