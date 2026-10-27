import threading

from ytpd.lmstudio.lm_studio_error import LmStudioError
from ytpd.lmstudio.lm_studio_model_load_client import LmStudioModelLoadClient
from ytpd.lmstudio.lm_studio_settings import LmStudioSettings
from ytpd.ports.lm_studio_model_loader import LmStudioModelLoader


class LmStudioRuntimeCoordinator:
    """Unload then load the LM Studio model once before the first match chat."""

    def __init__(
        self,
        settings: LmStudioSettings,
        load_client: LmStudioModelLoader | None = None,
    ) -> None:
        self._settings = settings
        self._load_client = load_client or LmStudioModelLoadClient(settings)
        self._lock = threading.Lock()
        self._ready = False

    def ensure_ready(self) -> None:
        """Force a clean load so chat requests inherit a known model runtime."""
        with self._lock:
            if self._ready:
                return
            self._reload_model()
            self._ready = True

    def release(self) -> None:
        """Unload the model after matching so download/transcode can use the GPU."""
        with self._lock:
            try:
                self._load_client.unload_model()
            except LmStudioError:
                pass
            self._ready = False

    def _reload_model(self) -> None:
        # Best-effort: older LM Studio builds may lack native load/unload.
        # Per-request reasoning_effort / chat_template_kwargs still apply.
        try:
            self._load_client.unload_model()
            self._load_client.load_model()
        except LmStudioError:
            return
