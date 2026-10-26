from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from ytpd.config.app_config import AppConfig
from ytpd.config.app_config_store import AppConfigStore
from ytpd.config.path_validator import PathValidator
from ytpd.jobs.job_store import JobStore
from ytpd.jobs.sqlite_job_checkpoint_store import SqliteJobCheckpointStore
from ytpd.web.app_factory import AppFactory
from ytpd.web.static_directory import StaticDirectory
from ytpd.web.template_directory import TemplateDirectory


def _build_app(tmp_path: Path) -> FastAPI:
    store = AppConfigStore(tmp_path / "app.yaml", PathValidator())
    config = store.save(
        AppConfig(
            host="127.0.0.1",
            port=8765,
            work_dir=Path("work"),
            dest_dir=Path("out"),
        )
    )
    return AppFactory(
        TemplateDirectory().resolve(),
        StaticDirectory().resolve(),
        config,
        store,
        JobStore(SqliteJobCheckpointStore(tmp_path / "jobs.db")),
    ).build()


def test_index_contains_all_tabs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    client = TestClient(_build_app(tmp_path))
    response = client.get("/")
    assert response.status_code == 200
    assert 'data-tab="job"' in response.text
    assert 'data-tab="progress"' in response.text
    assert 'data-tab="config"' in response.text
    assert 'data-tab="catalogue"' in response.text
    assert 'href="/static/css/tokens.css"' in response.text


def test_config_api_round_trip(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    client = TestClient(_build_app(tmp_path))
    get_response = client.get("/api/config")
    assert get_response.status_code == 200
    payload = get_response.json()
    payload["work_dir"] = "work2"
    payload["dest_dir"] = "out2"
    put_response = client.put("/api/config", json=payload)
    assert put_response.status_code == 200
    body = put_response.json()
    assert body["work_dir"] == "work2"
    assert (tmp_path / "work2").is_dir()
