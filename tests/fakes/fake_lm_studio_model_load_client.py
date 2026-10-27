from ytpd.lmstudio.lm_studio_error import LmStudioError


class FakeLmStudioModelLoadClient:
    """Recording LM Studio load/unload double for unit tests."""

    def __init__(self, fail_load: bool = False) -> None:
        self.load_calls = 0
        self.unload_calls = 0
        self._fail_load = fail_load

    def load_model(self) -> None:
        """Record a load; optionally raise to simulate API failure."""
        self.load_calls += 1
        if self._fail_load:
            raise LmStudioError("LM Studio /api/v1/models/load a renvoyé HTTP 404")

    def unload_model(self) -> None:
        """Record an unload."""
        self.unload_calls += 1
