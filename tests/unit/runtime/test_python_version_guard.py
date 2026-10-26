import pytest

from ytpd.runtime.interpreter_version import InterpreterVersion
from ytpd.runtime.python_version_guard import PythonVersionGuard
from ytpd.runtime.unsupported_python_version_error import UnsupportedPythonVersionError


def test_accepts_python_314_without_gil_warning_when_gil_disabled() -> None:
    guard = PythonVersionGuard()
    warning = guard.check(
        InterpreterVersion(major=3, minor=14, micro=7, gil_enabled=False)
    )
    assert warning is None


def test_warns_when_gil_enabled() -> None:
    guard = PythonVersionGuard()
    warning = guard.check(
        InterpreterVersion(major=3, minor=14, micro=7, gil_enabled=True)
    )
    assert warning is not None
    assert "GIL" in warning


def test_rejects_other_minor() -> None:
    guard = PythonVersionGuard()
    with pytest.raises(UnsupportedPythonVersionError) as raised:
        guard.check(
            InterpreterVersion(major=3, minor=13, micro=0, gil_enabled=None)
        )
    assert "3.14" in str(raised.value)
    assert "3.13" in str(raised.value)


def test_rejects_other_major() -> None:
    guard = PythonVersionGuard()
    with pytest.raises(UnsupportedPythonVersionError):
        guard.check(
            InterpreterVersion(major=2, minor=14, micro=0, gil_enabled=None)
        )
