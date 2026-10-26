import ast
from pathlib import Path

from python_guardrails.guard_violation import GuardViolation
from python_guardrails.scan_paths import (
    DEFAULT_SKIPPED_PARTS,
    iter_python_files,
    preceding_lines_contain_marker,
)

SOLID_FUNCTION_MAX_LINES_MARKER = "solid-function-max-lines:"


class FunctionLineLimitGuard:
    """Max lines per function/method body (AST end_lineno - lineno)."""

    def __init__(
        self,
        max_lines: int = 60,
        skipped_parts: frozenset[str] | None = None,
        skip_tests: bool = True,
    ) -> None:
        self._max_lines = max_lines
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
        lines = source.splitlines()
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as error:
            return [GuardViolation(path=path, kind="syntax_error", detail=str(error))]

        found: list[GuardViolation] = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            start = int(node.lineno or 0)
            end = int(node.end_lineno or start)
            body_lines = end - start + 1
            if body_lines <= self._max_lines:
                continue
            if preceding_lines_contain_marker(
                lines, start, SOLID_FUNCTION_MAX_LINES_MARKER
            ):
                continue
            found.append(
                GuardViolation(
                    path=path,
                    kind="function_max_lines",
                    detail=(
                        f"{node.name}: {body_lines} lines > {self._max_lines}"
                    ),
                )
            )
        return found
