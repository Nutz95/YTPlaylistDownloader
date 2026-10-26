class FakeResourceGate:
    """Record LLM/GPU acquisitions for gate unit tests."""

    def __init__(self) -> None:
        self.llm_held = False
        self.gpu_holders = 0
        self.llm_acquire_count = 0
        self.gpu_acquire_count = 0

    def acquire_llm(self) -> None:
        """Mark the LLM slot as held."""
        self.llm_held = True
        self.llm_acquire_count += 1

    def release_llm(self) -> None:
        """Release the LLM slot."""
        self.llm_held = False

    def try_acquire_gpu(self) -> bool:
        """Take a GPU slot unless LLM is held."""
        if self.llm_held:
            return False
        self.gpu_holders += 1
        self.gpu_acquire_count += 1
        return True

    def release_gpu(self) -> None:
        """Release one GPU slot."""
        if self.gpu_holders > 0:
            self.gpu_holders -= 1
