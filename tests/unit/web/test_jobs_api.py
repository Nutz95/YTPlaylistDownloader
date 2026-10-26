from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ytpd.config.app_config import AppConfig
from ytpd.config.app_config_store import AppConfigStore
from ytpd.config.path_validator import PathValidator
from ytpd.jobs.job_store import JobStore
from ytpd.jobs.sqlite_job_checkpoint_store import SqliteJobCheckpointStore
from ytpd.web.app_factory import AppFactory
from ytpd.web.static_directory import StaticDirectory
from ytpd.web.template_directory import TemplateDirectory


def _build_client(tmp_path: Path) -> TestClient:
    store = AppConfigStore(tmp_path / "app.yaml", PathValidator())
    config = store.save(
        AppConfig(
            host="127.0.0.1",
            port=8765,
            work_dir=Path("work"),
            dest_dir=Path("out"),
        )
    )
    job_store = JobStore(SqliteJobCheckpointStore(tmp_path / "jobs.db"))
    app = AppFactory(
        TemplateDirectory().resolve(),
        StaticDirectory().resolve(),
        config,
        store,
        job_store,
    ).build()
    return TestClient(app)


def test_create_and_get_job(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    client = _build_client(tmp_path)
    created = client.post("/api/jobs", json={"url": "https://youtu.be/abc"})
    assert created.status_code == 201
    body = created.json()
    assert body["status"] == "queued"
    assert body["tracks"] == []
    fetched = client.get(f"/api/jobs/{body['job_id']}")
    assert fetched.status_code == 200
    assert fetched.json()["source_url"] == "https://youtu.be/abc"
