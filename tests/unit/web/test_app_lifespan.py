import asyncio

from fastapi import FastAPI

from tests.fakes.fake_lm_studio_model_runtime import FakeLmStudioModelRuntime
from tests.fakes.fake_pipeline_runner import FakePipelineRunner
from ytpd.web.app_lifespan import AppLifespan


def test_lifespan_drains_on_start_and_cancels_on_shutdown() -> None:
    runner = FakePipelineRunner()
    lm_runtime = FakeLmStudioModelRuntime()
    lifespan = AppLifespan(runner, lm_runtime)

    async def _run() -> None:
        async with lifespan.handle(FastAPI()):
            assert runner.drain_calls == 1
            assert runner.cancel_calls == 0
            assert lm_runtime.release_calls == 0

    asyncio.run(_run())
    assert runner.drain_calls == 1
    assert runner.cancel_calls == 1
    assert lm_runtime.release_calls == 1
