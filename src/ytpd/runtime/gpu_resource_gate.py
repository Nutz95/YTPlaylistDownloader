import threading


class GpuResourceGate:
    """Serialize LLM work against GPU transcode slots."""

    def __init__(self) -> None:
        self._condition = threading.Condition()
        self._llm_held = False
        self._gpu_holders = 0

    def acquire_llm(self) -> None:
        """Block until no GPU holders remain, then take the LLM slot."""
        with self._condition:
            while self._llm_held or self._gpu_holders > 0:
                self._condition.wait()
            self._llm_held = True

    def release_llm(self) -> None:
        """Release the LLM slot and wake waiters."""
        with self._condition:
            self._llm_held = False
            self._condition.notify_all()

    def try_acquire_gpu(self) -> bool:
        """Take a GPU slot when LLM is idle; otherwise return false."""
        with self._condition:
            if self._llm_held:
                return False
            self._gpu_holders += 1
            return True

    def release_gpu(self) -> None:
        """Release one GPU slot and wake waiters."""
        with self._condition:
            if self._gpu_holders <= 0:
                return
            self._gpu_holders -= 1
            self._condition.notify_all()
