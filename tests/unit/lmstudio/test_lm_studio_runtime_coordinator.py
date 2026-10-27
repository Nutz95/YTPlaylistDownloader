from tests.fakes.fake_lm_studio_model_load_client import FakeLmStudioModelLoadClient
from ytpd.lmstudio.lm_studio_runtime_coordinator import LmStudioRuntimeCoordinator
from ytpd.lmstudio.lm_studio_settings import LmStudioSettings


def _settings() -> LmStudioSettings:
    return LmStudioSettings(
        base_url="http://127.0.0.1:1234/v1",
        model="test-model",
        timeout_sec=1.0,
        context_length=8192,
    )


def test_ensure_ready_unloads_then_loads_once() -> None:
    load_client = FakeLmStudioModelLoadClient()
    coordinator = LmStudioRuntimeCoordinator(_settings(), load_client)
    coordinator.ensure_ready()
    coordinator.ensure_ready()
    assert load_client.unload_calls == 1
    assert load_client.load_calls == 1


def test_ensure_ready_tolerates_load_failure() -> None:
    load_client = FakeLmStudioModelLoadClient(fail_load=True)
    coordinator = LmStudioRuntimeCoordinator(_settings(), load_client)
    coordinator.ensure_ready()
    assert load_client.unload_calls == 1
    assert load_client.load_calls == 1


def test_release_unloads_and_allows_reload() -> None:
    load_client = FakeLmStudioModelLoadClient()
    coordinator = LmStudioRuntimeCoordinator(_settings(), load_client)
    coordinator.ensure_ready()
    coordinator.release()
    assert load_client.unload_calls == 2
    assert load_client.load_calls == 1
    coordinator.ensure_ready()
    assert load_client.unload_calls == 3
    assert load_client.load_calls == 2
