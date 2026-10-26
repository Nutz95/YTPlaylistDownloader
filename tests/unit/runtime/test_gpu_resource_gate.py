from ytpd.runtime.gpu_resource_gate import GpuResourceGate


def test_gpu_acquire_blocked_while_llm_held() -> None:
    gate = GpuResourceGate()
    gate.acquire_llm()
    assert gate.try_acquire_gpu() is False
    gate.release_llm()
    assert gate.try_acquire_gpu() is True
    gate.release_gpu()


def test_gpu_slot_allows_llm_after_release() -> None:
    gate = GpuResourceGate()
    assert gate.try_acquire_gpu() is True
    gate.release_gpu()
    gate.acquire_llm()
    assert gate.try_acquire_gpu() is False
    gate.release_llm()
