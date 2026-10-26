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


def test_to_storage_path_keeps_relative_under_cwd(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    validator = PathValidator()
    absolute = validator.ensure_directory("_work")
    stored = validator.to_storage_path(absolute)
    assert not stored.is_absolute()
    assert stored.as_posix() == "_work"


def test_ensure_directory_rejects_parent_escape(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(InvalidAppConfigError):
        PathValidator().ensure_directory("../outside")
