from ytpd.runtime.interpreter_version import InterpreterVersion
from ytpd.runtime.unsupported_python_version_error import UnsupportedPythonVersionError

_REQUIRED_MAJOR = 3
_REQUIRED_MINOR = 14
_GIL_WARNING = (
    "Python 3.14 is running with the GIL enabled. "
    "Install a free-threaded 3.14 build for full thread parallelism."
)


class PythonVersionGuard:
    """Ensure the active interpreter matches the required Python release."""

    def __init__(
        self,
        required_major: int = _REQUIRED_MAJOR,
        required_minor: int = _REQUIRED_MINOR,
    ) -> None:
        self._required_major = required_major
        self._required_minor = required_minor

    def check(self, version: InterpreterVersion) -> str | None:
        """Validate version; return a GIL warning string or None when acceptable."""
        if version.major != self._required_major or version.minor != self._required_minor:
            raise UnsupportedPythonVersionError(
                "Python "
                f"{self._required_major}.{self._required_minor} is required; "
                f"found {version.major}.{version.minor}.{version.micro}."
            )
        if version.gil_enabled is True:
            return _GIL_WARNING
        return None
