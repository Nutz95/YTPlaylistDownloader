from pathlib import Path

import pytest

from ytpd.application_composer import ApplicationComposer


def test_composer_builds_app_and_settings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    composed = ApplicationComposer().compose()
    assert composed.settings.host == "127.0.0.1"
    assert composed.settings.port == 8765
    assert composed.app.title == "YTPlaylistDownloader"
    assert Path(composed.settings.work_dir).is_dir()
    assert Path(composed.settings.dest_dir).is_dir()
