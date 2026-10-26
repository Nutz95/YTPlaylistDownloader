from pathlib import Path

from fastapi import FastAPI

from ytpd.config.app_config import AppConfig
from ytpd.config.app_config_store import AppConfigStore
from ytpd.config.path_validator import PathValidator
from ytpd.jobs.job_resume_stack import JobResumeStack
from ytpd.jobs.progress_calculator import ProgressCalculator
from ytpd.jobs.sqlite_job_checkpoint_store import SqliteJobCheckpointStore
from ytpd.web.app_factory import AppFactory
from ytpd.web.static_directory import StaticDirectory
from ytpd.web.template_directory import TemplateDirectory


class BuildTestApp:
    """Compose a FastAPI app for offline unit tests under ``tmp_path``."""

    def build(self, tmp_path: Path) -> FastAPI:
        """Create app + relative config dirs inside ``tmp_path`` (caller chdirs)."""
        store = AppConfigStore(tmp_path / "app.yaml", PathValidator())
        config = store.save(
            AppConfig(
                host="127.0.0.1",
                port=8765,
                work_dir=Path("work"),
                dest_dir=Path("out"),
            )
        )
        resume_stack = JobResumeStack(
            SqliteJobCheckpointStore(tmp_path / "jobs.db"),
            tmp_path / "work",
            tmp_path / "out",
        )
        return AppFactory(
            TemplateDirectory().resolve(),
            StaticDirectory().resolve(),
            config,
            store,
            resume_stack.job_store,
            ProgressCalculator(),
            resume_stack.resume_service,
        ).build()
