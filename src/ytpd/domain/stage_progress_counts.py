from dataclasses import dataclass


@dataclass(frozen=True)
class StageProgressCounts:
    """How far the current pipeline stage has advanced."""

    done: int
    total: int
