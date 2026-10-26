import ast
from pathlib import Path

from python_guardrails.guard_violation import GuardViolation
from python_guardrails.scan_paths import DEFAULT_SKIPPED_PARTS, iter_python_files


class OwnedPositionalTupleGuard:
    """Ban namedtuple/NamedTuple for owned value objects."""

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
            if isinstance(node, ast.Call) and self._is_namedtuple_call(node):
                found.append(
                    GuardViolation(
                        path=path,
                        kind="namedtuple_call",
                        detail=f"line {node.lineno}: namedtuple(...)",
                    )
                )
            if isinstance(node, ast.ClassDef) and self._is_namedtuple_class(node):
                found.append(
                    GuardViolation(
                        path=path,
                        kind="namedtuple_class",
                        detail=f"line {node.lineno}: class {node.name}(NamedTuple)",
                    )
                )
        return found

    def _is_namedtuple_call(self, node: ast.Call) -> bool:
        func = node.func
        if isinstance(func, ast.Name) and func.id == "namedtuple":
            return True
        if isinstance(func, ast.Attribute) and func.attr == "namedtuple":
            return True
        return False

    def _is_namedtuple_class(self, node: ast.ClassDef) -> bool:
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == "NamedTuple":
                return True
            if isinstance(base, ast.Attribute) and base.attr == "NamedTuple":
                return True
        return False
