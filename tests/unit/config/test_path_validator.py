from pathlib import Path

import pytest

from ytpd.config.invalid_app_config_error import InvalidAppConfigError
from ytpd.config.path_validator import PathValidator


def test_ensure_directory_creates_relative_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    resolved = PathValidator().ensure_directory("nested/work")
    assert resolved.is_dir()
    assert resolved == (tmp_path / "nested" / "work").resolve()


def test_ensure_directory_rejects_empty() -> None:
    with pytest.raises(InvalidAppConfigError):
        PathValidator().ensure_directory("   ")
