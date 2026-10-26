from pathlib import Path

from fastapi.testclient import TestClient

from ytpd.config.app_config import AppConfig
from ytpd.config.app_config_store import AppConfigStore
from ytpd.config.path_validator import PathValidator
from ytpd.web.app_factory import AppFactory
from ytpd.web.static_directory import StaticDirectory
from ytpd.web.template_directory import TemplateDirectory


def test_index_contains_all_tabs(tmp_path: Path) -> None:
    store = AppConfigStore(tmp_path / "app.yaml", PathValidator())
    config = store.save(
        AppConfig(
            host="127.0.0.1",
            port=8765,
            work_dir=tmp_path / "work",
            dest_dir=tmp_path / "out",
        )
    )
    app = AppFactory(
        TemplateDirectory().resolve(),
        StaticDirectory().resolve(),
        config,
        store,
    ).build()
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert 'data-tab="job"' in response.text
    assert 'data-tab="progress"' in response.text
    assert 'data-tab="config"' in response.text
    assert 'data-tab="catalogue"' in response.text
    assert 'href="/static/css/tokens.css"' in response.text


def test_config_api_round_trip(tmp_path: Path) -> None:
    store = AppConfigStore(tmp_path / "app.yaml", PathValidator())
    config = store.save(
        AppConfig(
            host="127.0.0.1",
            port=8765,
            work_dir=tmp_path / "work",
            dest_dir=tmp_path / "out",
        )
    )
    app = AppFactory(
        TemplateDirectory().resolve(),
        StaticDirectory().resolve(),
        config,
        store,
    ).build()
    client = TestClient(app)
    get_response = client.get("/api/config")
    assert get_response.status_code == 200
    payload = get_response.json()
    payload["work_dir"] = (tmp_path / "work2").as_posix()
    payload["dest_dir"] = (tmp_path / "out2").as_posix()
    put_response = client.put("/api/config", json=payload)
    assert put_response.status_code == 200
    body = put_response.json()
    assert body["work_dir"].endswith("work2")
    assert Path(body["work_dir"]).is_dir()
