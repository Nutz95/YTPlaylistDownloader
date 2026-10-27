import httpx

from ytpd.lmstudio.lm_studio_api_root import LmStudioApiRoot
from ytpd.lmstudio.lm_studio_error import LmStudioError
from ytpd.lmstudio.lm_studio_settings import LmStudioSettings

_OFFLINE_MESSAGE = "LM Studio est hors ligne ou injoignable."
# Model load can far exceed a short chat timeout.
_LOAD_TIMEOUT_FLOOR_SEC = 300.0


class LmStudioModelLoadClient:
    """Call LM Studio native ``/api/v1/models/load`` and ``/unload`` endpoints."""

    def __init__(self, settings: LmStudioSettings) -> None:
        self._settings = settings
        self._api_root = LmStudioApiRoot().from_openai_base_url(settings.base_url)
        self._timeout = max(settings.timeout_sec, _LOAD_TIMEOUT_FLOOR_SEC)

    def load_model(self) -> None:
        """Load the configured model with the settings context length."""
        if self._settings.model.strip() == "":
            raise LmStudioError("model LM Studio requis pour load/unload")
        self._post_json(
            "/api/v1/models/load",
            {
                "model": self._settings.model,
                "context_length": self._settings.context_length,
                "echo_load_config": False,
            },
        )

    def unload_model(self) -> None:
        """Unload the configured model; ignore already-unloaded responses."""
        if self._settings.model.strip() == "":
            raise LmStudioError("model LM Studio requis pour load/unload")
        try:
            self._post_json(
                "/api/v1/models/unload",
                {"instance_id": self._settings.model},
            )
        except LmStudioError as error:
            if self._is_model_not_loaded_error(error):
                return
            raise

    def _post_json(self, path: str, payload: dict[str, str | int | bool]) -> None:
        url = f"{self._api_root}{path}"
        try:
            response = httpx.post(url, json=payload, timeout=self._timeout)
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            body = error.response.text
            raise LmStudioError(
                f"LM Studio {path} a renvoyé HTTP {error.response.status_code} : {body}"
            ) from error
        except httpx.HTTPError as error:
            raise LmStudioError(_OFFLINE_MESSAGE) from error

    @staticmethod
    def _is_model_not_loaded_error(error: LmStudioError) -> bool:
        message = str(error).casefold()
        return "404" in message or "not loaded" in message or "not found" in message
