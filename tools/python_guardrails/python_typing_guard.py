from pathlib import Path
import re

from python_guardrails.guard_violation import GuardViolation


class PythonTypingGuard:
    """Flags object/Any and bare dict/list/tuple/set annotations."""

    def __init__(
        self,
        skipped_parts: frozenset[str] | None = None,
    ) -> None:
        self._skipped_parts = skipped_parts or frozenset(
            {"__pycache__", ".venv", "site-packages", "node_modules"}
        )
        # Exclude runtime constructors like `values: list(...)` / `data: dict()`.
        self._patterns: list[tuple[str, re.Pattern[str]]] = [
            ("any_type", re.compile(r"(?:(?::|\|)\s*|->\s*)Any\b")),
            # Allow object.__setattr__; ban object used as an annotation type.
            ("object_type", re.compile(r"(?:(?::|\|)\s*|->\s*)object\b(?!\.)")),
            ("bare_dict", re.compile(r"(?:(?::|\|)\s*|->\s*)dict\b(?!\s*[\[(])")),
            ("bare_list", re.compile(r"(?:(?::|\|)\s*|->\s*)list\b(?!\s*[\[(])")),
            ("bare_tuple", re.compile(r"(?:(?::|\|)\s*|->\s*)tuple\b(?!\s*[\[(])")),
            ("bare_set", re.compile(r"(?:(?::|\|)\s*|->\s*)set\b(?!\s*[\[(])")),
            (
                "typing_any_import",
                re.compile(r"from\s+typing\s+import\s+[^\n]*\bAny\b"),
            ),
        ]

    def check(self, roots: list[Path]) -> list[GuardViolation]:
        """Scan roots and return guardrail violations."""
        violations: list[GuardViolation] = []
        for root in roots:
            for path in root.rglob("*.py"):
                if any(part in self._skipped_parts for part in path.parts):
                    continue
                if path.name == "__init__.py":
                    continue
                violations.extend(self._check_file(path))
        return violations

    def _check_file(self, path: Path) -> list[GuardViolation]:
        text = path.read_text(encoding="utf-8")
        found: list[GuardViolation] = []
        for kind, pattern in self._patterns:
            if pattern.search(text):
                found.append(
                    GuardViolation(
                        path=path,
                        kind=kind,
                        detail="use a concrete TypedDict/dataclass/list[T]/dict[K,V]",
                    )
                )
        return found
