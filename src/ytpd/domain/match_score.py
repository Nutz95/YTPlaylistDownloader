from dataclasses import dataclass


@dataclass(frozen=True)
class MatchScore:
    """Numeric score for one YouTube match candidate."""

    value: float
