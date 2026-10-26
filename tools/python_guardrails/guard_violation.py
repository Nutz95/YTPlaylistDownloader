from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class GuardViolation:
    """One guardrail finding at a path with a stable kind and detail message."""

    path: Path
    kind: str
    detail: str

