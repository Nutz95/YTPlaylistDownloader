from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from python_guardrails.guard_violation import GuardViolation


def count_violations_by_kind(violations: list[GuardViolation]) -> dict[str, int]:
    """Return sorted counts of violations keyed by kind."""
    counts: Counter[str] = Counter(item.kind for item in violations)
    return {kind: int(value) for kind, value in sorted(counts.items())}


def load_baseline(path: Path) -> dict[str, int]:
    """Load a JSON baseline map of kind -> allowed count (empty if missing)."""
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {str(key): int(value) for key, value in payload.items()}


def write_baseline(path: Path, counts: dict[str, int]) -> None:
    """Persist a sorted kind -> count baseline JSON next to the given path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = {key: int(counts[key]) for key in sorted(counts)}
    path.write_text(
        json.dumps(ordered, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def assert_within_baseline(
    violations: list[GuardViolation],
    baseline_path: Path,
    *,
    update: bool = False,
) -> None:
    """Fail if any kind count exceeds the baseline JSON (progressive ratchet)."""
    current = count_violations_by_kind(violations)
    if update:
        existing = load_baseline(baseline_path)
        existing.update(current)
        write_baseline(baseline_path, existing)
        return

    baseline = load_baseline(baseline_path)
    regressions: list[str] = []
    for kind, count in current.items():
        allowed = int(baseline.get(kind, 0))
        if count > allowed:
            regressions.append(
                f"{kind}: {count} > baseline {allowed} (+{count - allowed})"
            )
    for kind, allowed in baseline.items():
        if kind not in current and int(allowed) < 0:
            continue
    if regressions:
        raise AssertionError(
            "Guardrail baseline regressions:\n- "
            + "\n- ".join(regressions)
            + f"\nBaseline file: {baseline_path}"
        )
