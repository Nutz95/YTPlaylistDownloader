from dataclasses import dataclass


@dataclass(frozen=True)
class SiblingProcessTerminationReport:
    """PIDs of previous ytpd server processes terminated at startup."""

    killed_pids: list[int]
