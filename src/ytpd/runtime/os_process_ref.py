from dataclasses import dataclass


@dataclass(frozen=True)
class OsProcessRef:
    """One OS process with its command line for sibling detection."""

    pid: int
    command_line: str
