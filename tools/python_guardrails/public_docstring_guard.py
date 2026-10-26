import ast
from pathlib import Path

from python_guardrails.guard_violation import GuardViolation
from python_guardrails.scan_paths import (
    DEFAULT_SKIPPED_PARTS,
    iter_python_files,
    preceding_lines_contain_marker,
)

SOLID_NO_DOCSTRING_MARKER = "solid-no-docstring:"


class PublicDocstringGuard:
    """Require docstrings on public classes, enums, and public functions/methods."""

    def __init__(
        self,
        skipped_parts: frozenset[str] | None = None,
        skip_tests: bool = True,
    ) -> None:
        self._skipped_parts = skipped_parts or DEFAULT_SKIPPED_PARTS
        self._skip_tests = skip_tests

    def check(self, roots: list[Path]) -> list[GuardViolation]:
        """Scan roots and return missing-public-docstring violations."""
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
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and self._is_public_name(node.name):
                found.extend(self._check_class(path, lines, node))
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if self._is_public_name(node.name) and not self._is_dunder(node.name):
                    found.extend(
                        self._check_callable(
                            path,
                            lines,
                            node,
                            kind="missing_public_function_docstring",
                        )
                    )
        return found

    def _check_class(
        self,
        path: Path,
        lines: list[str],
        node: ast.ClassDef,
    ) -> list[GuardViolation]:
        found: list[GuardViolation] = []
        if not self._has_docstring(node):
            if not preceding_lines_contain_marker(
                lines, int(node.lineno or 0), SOLID_NO_DOCSTRING_MARKER
            ):
                found.append(
                    GuardViolation(
                        path=path,
                        kind="missing_public_type_docstring",
                        detail=(
                            f"line {node.lineno}: public type {node.name} "
                            "needs a docstring"
                        ),
                    )
                )
        for child in node.body:
            if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not self._is_public_name(child.name):
                continue
            if self._is_dunder(child.name):
                continue
            found.extend(
                self._check_callable(
                    path,
                    lines,
                    child,
                    kind="missing_public_method_docstring",
                )
            )
        return found

    def _check_callable(
        self,
        path: Path,
        lines: list[str],
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        *,
        kind: str,
    ) -> list[GuardViolation]:
        if self._has_docstring(node):
            return []
        if preceding_lines_contain_marker(
            lines, int(node.lineno or 0), SOLID_NO_DOCSTRING_MARKER
        ):
            return []
        return [
            GuardViolation(
                path=path,
                kind=kind,
                detail=(
                    f"line {node.lineno}: public callable {node.name} "
                    "needs a docstring"
                ),
            )
        ]

    def _has_docstring(self, node: ast.AST) -> bool:
        return ast.get_docstring(node) is not None

    def _is_public_name(self, name: str) -> bool:
        return not name.startswith("_")

    def _is_dunder(self, name: str) -> bool:
        return name.startswith("__") and name.endswith("__")
