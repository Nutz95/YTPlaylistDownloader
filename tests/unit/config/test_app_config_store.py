from pathlib import Path

import pytest

from ytpd.config.app_config import AppConfig
from ytpd.config.app_config_store import AppConfigStore
from ytpd.config.invalid_app_config_error import InvalidAppConfigError
from ytpd.config.path_validator import PathValidator


def test_save_and_reload_persists_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    writable = tmp_path / "config" / "app.yaml"
    store = AppConfigStore(writable, PathValidator())
    saved = store.save(
        AppConfig(
            host="127.0.0.1",
            port=8765,
            work_dir=Path("work_data"),
            dest_dir=Path("out_data"),
            lm_base_url="http://127.0.0.1:1234/v1",
            lm_model="test-model",
            lm_timeout_sec=30.0,
            youtube_cookies_from_browser="brave",
            youtube_cookies_file="config/youtube_cookies.txt",
            ffmpeg_path="",
        )
    )
    assert writable.is_file()
    assert saved.work_dir.is_dir()
    assert saved.dest_dir.is_dir()
    reloaded = store.load()
    assert reloaded.host == "127.0.0.1"
    assert reloaded.port == 8765
    assert not saved.work_dir.is_absolute()
    assert not saved.dest_dir.is_absolute()
    assert reloaded.work_dir == saved.work_dir
    assert reloaded.dest_dir == saved.dest_dir
    assert saved.work_dir.as_posix() == "work_data"
    assert saved.dest_dir.as_posix() == "out_data"
    assert reloaded.youtube_cookies_from_browser == "brave"
    assert reloaded.youtube_cookies_file == "config/youtube_cookies.txt"
    assert reloaded.ffmpeg_path == ""


def test_cookies_default_from_packaged_yaml_when_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    store = AppConfigStore(tmp_path / "app.yaml", PathValidator())
    loaded = store.load_text(
        "\n".join(
            [
                'bind_host: "127.0.0.1"',
                "bind_port: 8765",
                'work_dir: "_work"',
                'dest_dir: "_out"',
                'lm_base_url: "http://127.0.0.1:1234/v1"',
                'lm_model: "m"',
                "lm_timeout_sec: 30",
            ]
        )
    )
    assert loaded.youtube_cookies_from_browser == "brave"
    assert loaded.youtube_cookies_file == ""
    assert loaded.ffmpeg_path == ""


def test_rejects_empty_host() -> None:
    store = AppConfigStore(Path("unused.yaml"), PathValidator())
    with pytest.raises(InvalidAppConfigError):
        store.load_text(
            "\n".join(
                [
                    'bind_host: ""',
                    "bind_port: 8765",
                    'work_dir: "_work"',
                    'dest_dir: "_out"',
                    "",
                ]
            )
        )
