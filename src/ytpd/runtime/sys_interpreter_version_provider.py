import sys

from ytpd.runtime.interpreter_version import InterpreterVersion


class SysInterpreterVersionProvider:
    """Read interpreter version details from the running ``sys`` module."""

    def read(self) -> InterpreterVersion:
        """Return major/minor/micro and GIL status when the runtime exposes it."""
        info = sys.version_info
        return InterpreterVersion(
            major=info.major,
            minor=info.minor,
            micro=info.micro,
            gil_enabled=self._read_gil_enabled(),
        )

    def _read_gil_enabled(self) -> bool | None:
        # solid-getattr: optional CPython free-threading probe (3.13+)
        gil_probe = getattr(sys, "_is_gil_enabled", None)
        if gil_probe is None:
            return None
        return bool(gil_probe())
