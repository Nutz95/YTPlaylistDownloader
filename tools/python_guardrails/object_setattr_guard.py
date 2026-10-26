import ast
from pathlib import Path

from python_guardrails.guard_violation import GuardViolation
from python_guardrails.scan_paths import DEFAULT_SKIPPED_PARTS, iter_python_files


class ObjectSetattrGuard:
    """Ban ``object.__setattr__`` / ``setattr``; prefer non-frozen copies or tuples."""

    def __init__(
        self,
        skipped_parts: frozenset[str] | None = None,
        skip_tests: bool = True,
    ) -> None:
        self._skipped_parts = skipped_parts or DEFAULT_SKIPPED_PARTS
        self._skip_tests = skip_tests

    def check(self, roots: list[Path]) -> list[GuardViolation]:
        """Scan roots and return guardrail violations."""
        violations: list[GuardViolation] = []
        for path in iter_python_files(
            roots,
            skipped_parts=self._skipped_parts,
            skip_tests=self._skip_tests,
        ):
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
            if self._is_object_setattr(node):
                found.append(
                    GuardViolation(
                        path=path,
                        kind="object_setattr",
                        detail=(
                            f"line {node.lineno}: object.__setattr__(...); "
                            "use a non-frozen dataclass copy or tuple fields"
                        ),
                    )
                )
            if self._is_builtin_setattr(node):
                found.append(
                    GuardViolation(
                        path=path,
                        kind="setattr_call",
                        detail=f"line {node.lineno}: setattr(...)",
                    )
                )
        return found

    def _is_object_setattr(self, node: ast.Call) -> bool:
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr != "__setattr__":
            return False
        return isinstance(func.value, ast.Name) and func.value.id == "object"

    def _is_builtin_setattr(self, node: ast.Call) -> bool:
        return isinstance(node.func, ast.Name) and node.func.id == "setattr"
