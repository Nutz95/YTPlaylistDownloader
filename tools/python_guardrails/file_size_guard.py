import ast
from pathlib import Path
import re

from python_guardrails.guard_violation import GuardViolation


class FileSizeGuard:
    """Enforces max lines per file and max methods per class."""

    def __init__(
        self,
        max_lines: int = 400,
        max_methods_per_class: int = 30,
        suffixes: frozenset[str] | None = None,
        skipped_parts: frozenset[str] | None = None,
    ) -> None:
        self._max_lines = max_lines
        self._max_methods = max_methods_per_class
        self._suffixes = suffixes or frozenset({".py", ".js", ".css", ".html"})
        self._skipped_parts = skipped_parts or frozenset(
            {"__pycache__", ".venv", "site-packages", "static", "node_modules"}
        )
        self._js_method_pattern = re.compile(
            r"^\s{2}(?:async\s+)?(?:_?[a-zA-Z]\w*)\s*\("
        )

    def check(self, roots: list[Path]) -> list[GuardViolation]:
        """Scan roots and return guardrail violations."""
        violations: list[GuardViolation] = []
        for root in roots:
            for path in root.rglob("*"):
                if not path.is_file():
                    continue
                if any(part in self._skipped_parts for part in path.parts):
                    continue
                if path.suffix not in self._suffixes:
                    continue
                if "bundle" in path.name:
                    continue
                violations.extend(self._check_file(path))
        return violations

    def _check_file(self, path: Path) -> list[GuardViolation]:
        lines = path.read_text(encoding="utf-8").splitlines()
        found: list[GuardViolation] = []
        if len(lines) > self._max_lines:
            found.append(
                GuardViolation(
                    path=path,
                    kind="lines",
                    detail=f"{len(lines)} lines > {self._max_lines}",
                )
            )
        if path.suffix == ".py":
            found.extend(self._check_python_methods(path, lines))
        if path.suffix == ".js":
            found.extend(self._check_js_methods(path, lines))
        return found

    def _check_python_methods(
        self,
        path: Path,
        lines: list[str],
    ) -> list[GuardViolation]:
        del lines  # AST path; signature kept for call-site compatibility
        source = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError:
            return []
        violations: list[GuardViolation] = []
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            method_count = sum(
                1
                for child in node.body
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            )
            if method_count > self._max_methods:
                violations.append(
                    GuardViolation(
                        path=path,
                        kind="methods",
                        detail=(
                            f"{node.name} has {method_count} methods "
                            f"> {self._max_methods}"
                        ),
                    )
                )
        return violations

    def _check_js_methods(
        self,
        path: Path,
        lines: list[str],
    ) -> list[GuardViolation]:
        in_class = False
        class_name = ""
        method_count = 0
        violations: list[GuardViolation] = []
        for line in lines:
            if "class " in line and "{" in line:
                if in_class and method_count > self._max_methods:
                    violations.append(
                        GuardViolation(
                            path=path,
                            kind="methods",
                            detail=(
                                f"{class_name} has {method_count} methods "
                                f"> {self._max_methods}"
                            ),
                        )
                    )
                class_name = line.strip().split("class ", 1)[-1].split(" ", 1)[0]
                in_class = True
                method_count = 0
                continue
            if in_class and self._js_method_pattern.match(line):
                method_count += 1
        if in_class and method_count > self._max_methods:
            violations.append(
                GuardViolation(
                    path=path,
                    kind="methods",
                    detail=(
                        f"{class_name} has {method_count} methods "
                        f"> {self._max_methods}"
                    ),
                )
            )
        return violations
