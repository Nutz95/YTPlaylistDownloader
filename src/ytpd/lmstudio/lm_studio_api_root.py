class LmStudioApiRoot:
    """Derive LM Studio native API root from an OpenAI-compatible base URL."""

    def from_openai_base_url(self, base_url: str) -> str:
        """Strip a trailing ``/v1`` so ``/api/v1/...`` paths resolve correctly."""
        root = base_url.rstrip("/")
        if root.endswith("/v1"):
            return root[:-3]
        return root
