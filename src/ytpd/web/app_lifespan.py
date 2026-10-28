from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from ytpd.jobs.job_pipeline_runner import JobPipelineRunner
from ytpd.ports.lm_studio_model_runtime import LmStudioModelRuntime


class AppLifespan:
    """FastAPI lifespan: drain queued jobs on start; cancel and unload on stop."""

    def __init__(
        self,
        pipeline_runner: JobPipelineRunner,
        lm_runtime: LmStudioModelRuntime,
    ) -> None:
        self._pipeline_runner = pipeline_runner
        self._lm_runtime = lm_runtime

    @asynccontextmanager
    async def handle(self, _app: FastAPI) -> AsyncIterator[None]:
        """Drain the job queue at startup; cancel work and release the model on exit."""
        self._pipeline_runner.drain_queue()
        yield
        self._pipeline_runner.cancel()
        self._lm_runtime.release()
