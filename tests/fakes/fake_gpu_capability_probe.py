class FakeGpuCapabilityProbe:
    """Configurable GPU capability double for offline backend detection tests."""

    def __init__(self, nvidia: bool = False, arc: bool = False) -> None:
        self._nvidia = nvidia
        self._arc = arc

    def has_nvidia(self) -> bool:
        """Return the configured NVIDIA availability."""
        return self._nvidia

    def has_arc(self) -> bool:
        """Return the configured Arc availability."""
        return self._arc
