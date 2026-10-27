from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from ytpd.jobs.job_pipeline_runner import JobPipelineRunner
from ytpd.ports.lm_studio_model_runtime import LmStudioModelRuntime


class AppLifespan:
    """FastAPI lifespan: cancel pipeline and unload LM Studio on shutdown."""

    def __init__(
        self,
        pipeline_runner: JobPipelineRunner,
        lm_runtime: LmStudioModelRuntime,
    ) -> None:
        self._pipeline_runner = pipeline_runner
        self._lm_runtime = lm_runtime

    @asynccontextmanager
    async def handle(self, _app: FastAPI) -> AsyncIterator[None]:
        """Yield while the app runs; cancel work and release the model on exit."""
        yield
        self._pipeline_runner.cancel()
        self._lm_runtime.release()
