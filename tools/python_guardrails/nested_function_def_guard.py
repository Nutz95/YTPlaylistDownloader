import ast
from pathlib import Path

from python_guardrails.guard_violation import GuardViolation
from python_guardrails.scan_paths import (
    DEFAULT_SKIPPED_PARTS,
    iter_python_files,
    preceding_lines_contain_marker,
)

SOLID_NESTED_DEF_MARKER = "solid-nested-def:"


class NestedFunctionDefGuard:
    """Ban nested def/async def in production modules."""

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
        lines = source.splitlines()
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as error:
            return [GuardViolation(path=path, kind="syntax_error", detail=str(error))]

        parents = self._build_parent_map(tree)
        found: list[GuardViolation] = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            enclosing = self._enclosing_function(node, parents)
            if enclosing is None:
                continue
            if preceding_lines_contain_marker(
                lines, int(node.lineno or 0), SOLID_NESTED_DEF_MARKER
            ):
                continue
            found.append(
                GuardViolation(
                    path=path,
                    kind="nested_function_def",
                    detail=(
                        f"line {node.lineno}: nested {node.name} "
                        f"inside {enclosing.name}"
                    ),
                )
            )
        return found

    def _build_parent_map(self, root: ast.AST) -> dict[ast.AST, ast.AST]:
        parents: dict[ast.AST, ast.AST] = {}
        for parent in ast.walk(root):
            for child in ast.iter_child_nodes(parent):
                parents[child] = parent
        return parents

    def _enclosing_function(
        self,
        node: ast.AST,
        parents: dict[ast.AST, ast.AST],
    ) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
        current = parents.get(node)
        while current is not None:
            if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
                return current
            current = parents.get(current)
        return None
