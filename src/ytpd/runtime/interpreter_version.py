from dataclasses import dataclass


@dataclass(frozen=True)
class InterpreterVersion:
    """Interpreter major/minor/micro plus optional GIL-enabled flag."""

    major: int
    minor: int
    micro: int
    gil_enabled: bool | None
