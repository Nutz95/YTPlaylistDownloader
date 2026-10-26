import ast
from pathlib import Path

from python_guardrails.guard_violation import GuardViolation
from python_guardrails.scan_paths import DEFAULT_SKIPPED_PARTS, iter_python_files


class MonkeypatchSetattrGuard:
    """Prefer DI over monkeypatch.setattr on collaborators in tests."""

    def __init__(
        self,
        skipped_parts: frozenset[str] | None = None,
    ) -> None:
        self._skipped_parts = skipped_parts or DEFAULT_SKIPPED_PARTS

    def check(self, roots: list[Path]) -> list[GuardViolation]:
        """Scan roots and return guardrail violations."""
        violations: list[GuardViolation] = []
        for path in iter_python_files(
            roots,
            skipped_parts=self._skipped_parts,
            skip_tests=False,
        ):
            if "tests" not in path.parts and not path.name.startswith("test_"):
                continue
            violations.extend(self._check_file(path))
        return violations

    def _check_file(self, path: Path) -> list[GuardViolation]:
        source = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as error:
            return [GuardViolation(path=path, kind="syntax_error", detail=str(error))]

        found: list[GuardViolation] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr == "setattr":
                if isinstance(func.value, ast.Name) and "monkeypatch" in func.value.id:
                    found.append(
                        GuardViolation(
                            path=path,
                            kind="monkeypatch_setattr",
                            detail=f"line {node.lineno}: monkeypatch.setattr(...)",
                        )
                    )
        return found
