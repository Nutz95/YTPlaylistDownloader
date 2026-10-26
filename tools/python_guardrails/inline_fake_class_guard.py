import ast
from pathlib import Path

from python_guardrails.guard_violation import GuardViolation
from python_guardrails.scan_paths import DEFAULT_SKIPPED_PARTS, iter_python_files


class InlineFakeClassGuard:
    """Fakes belong under tests/fakes/; ban Fake/Dummy classes in test modules."""

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
            skip_init=True,
            skip_tests=False,
        ):
            if not self._is_test_module(path):
                continue
            if "fakes" in path.parts:
                violations.extend(self._check_fakes_file(path))
                continue
            violations.extend(self._check_test_module(path))
        return violations

    def _is_test_module(self, path: Path) -> bool:
        name = path.name
        if name.startswith("test_") or name.endswith("_test.py"):
            return True
        if name.endswith("_test_support.py") or name.endswith("_test_fakes.py"):
            return True
        return "tests" in path.parts

    def _check_test_module(self, path: Path) -> list[GuardViolation]:
        source = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as error:
            return [GuardViolation(path=path, kind="syntax_error", detail=str(error))]

        found: list[GuardViolation] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            if node.name.startswith("Test"):
                continue
            if self._looks_like_fake(node.name):
                found.append(
                    GuardViolation(
                        path=path,
                        kind="inline_fake_class",
                        detail=f"move {node.name} to tests/fakes/",
                    )
                )
            elif node in tree.body:
                found.append(
                    GuardViolation(
                        path=path,
                        kind="class_in_test_module",
                        detail=(
                            f"non-Test class {node.name} in test module; "
                            "prefer tests/fakes/ or pytest Test*"
                        ),
                    )
                )
        return found

    def _check_fakes_file(self, path: Path) -> list[GuardViolation]:
        source = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as error:
            return [GuardViolation(path=path, kind="syntax_error", detail=str(error))]

        classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
        found: list[GuardViolation] = []
        if len(classes) > 1:
            found.append(
                GuardViolation(
                    path=path,
                    kind="multi_fake_classes_per_file",
                    detail=f"{len(classes)} classes in fakes file",
                )
            )
        for node in classes:
            for child in node.body:
                if isinstance(child, ast.ClassDef):
                    found.append(
                        GuardViolation(
                            path=path,
                            kind="nested_class_in_fakes",
                            detail=f"nested {child.name} inside {node.name}",
                        )
                    )
        return found

    def _looks_like_fake(self, name: str) -> bool:
        lowered = name.lower()
        return "fake" in lowered or "dummy" in lowered
