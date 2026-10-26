import ast
from pathlib import Path

from python_guardrails.guard_violation import GuardViolation
from python_guardrails.scan_paths import (
    DEFAULT_SKIPPED_PARTS,
    iter_python_files,
    preceding_lines_contain_marker,
)

SOLID_GETATTR_MARKER = "solid-getattr:"


class DynamicAccessGuard:
    """Ban getattr/hasattr and except AttributeError in production-style trees."""

    def __init__(
        self,
        skipped_parts: frozenset[str] | None = None,
        allowlist_relative_paths: frozenset[str] | None = None,
        skip_tests: bool = True,
    ) -> None:
        self._skipped_parts = skipped_parts or DEFAULT_SKIPPED_PARTS
        self._allowlist = allowlist_relative_paths or frozenset()
        self._skip_tests = skip_tests

    def check(self, roots: list[Path]) -> list[GuardViolation]:
        """Scan roots and return guardrail violations."""
        violations: list[GuardViolation] = []
        for path in iter_python_files(
            roots,
            skipped_parts=self._skipped_parts,
            skip_tests=self._skip_tests,
        ):
            violations.extend(self._check_file(path, roots))
        return violations

    def _relative_key(self, path: Path, roots: list[Path]) -> str:
        for root in roots:
            try:
                return path.relative_to(root).as_posix()
            except ValueError:
                continue
        return path.as_posix()

    def _check_file(self, path: Path, roots: list[Path]) -> list[GuardViolation]:
        relative = self._relative_key(path, roots)
        source = path.read_text(encoding="utf-8")
        lines = source.splitlines()
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as error:
            return [GuardViolation(path=path, kind="syntax_error", detail=str(error))]

        found: list[GuardViolation] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in {"getattr", "hasattr"}:
                    if relative in self._allowlist:
                        continue
                    if preceding_lines_contain_marker(
                        lines, int(node.lineno or 0), SOLID_GETATTR_MARKER
                    ):
                        continue
                    found.append(
                        GuardViolation(
                            path=path,
                            kind="getattr_hasattr",
                            detail=f"line {node.lineno}: {node.func.id}(...)",
                        )
                    )
            if isinstance(node, ast.ExceptHandler) and self._catches_attribute_error(
                node
            ):
                found.append(
                    GuardViolation(
                        path=path,
                        kind="attribute_error_except",
                        detail=f"line {node.lineno}: except AttributeError",
                    )
                )
        return found

    def _catches_attribute_error(self, handler: ast.ExceptHandler) -> bool:
        exception_type = handler.type
        if exception_type is None:
            return False
        if isinstance(exception_type, ast.Name):
            return exception_type.id == "AttributeError"
        if isinstance(exception_type, ast.Tuple):
            return any(
                isinstance(entry, ast.Name) and entry.id == "AttributeError"
                for entry in exception_type.elts
            )
        return False
