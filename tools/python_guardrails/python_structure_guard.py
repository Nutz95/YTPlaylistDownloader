import ast
from pathlib import Path

from python_guardrails.guard_violation import GuardViolation


class PythonStructureGuard:
    """One type per file, no nested classes, no tuple piles (AST-based)."""

    def __init__(
        self,
        skipped_parts: frozenset[str] | None = None,
        allow_flask_response_tuple: bool = True,
    ) -> None:
        self._skipped_parts = skipped_parts or frozenset(
            {"__pycache__", ".venv", "site-packages", "node_modules"}
        )
        self._allow_flask_response_tuple = allow_flask_response_tuple

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
        source = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as error:
            return [
                GuardViolation(
                    path=path,
                    kind="syntax_error",
                    detail=str(error),
                )
            ]

        found: list[GuardViolation] = []
        type_names = [
            node.name
            for node in tree.body
            if isinstance(node, ast.ClassDef)
        ]
        if len(type_names) > 1:
            found.append(
                GuardViolation(
                    path=path,
                    kind="one_type_per_file",
                    detail=(
                        f"{len(type_names)} types in one file: "
                        + ", ".join(type_names)
                    ),
                )
            )

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for child in node.body:
                    if isinstance(child, ast.ClassDef):
                        found.append(
                            GuardViolation(
                                path=path,
                                kind="nested_class",
                                detail=(
                                    f"nested class {child.name} inside "
                                    f"{node.name}; extract to its own file"
                                ),
                            )
                        )
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                found.extend(self._check_function(path, node))
        return found

    def _check_function(
        self,
        path: Path,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> list[GuardViolation]:
        found: list[GuardViolation] = []
        for annotation in self._iter_annotations(node):
            if self._is_variadic_tuple(annotation):
                found.append(
                    GuardViolation(
                        path=path,
                        kind="variadic_tuple",
                        detail=(
                            f"{node.name}: use list[T] or a dataclass, "
                            "not a variadic tuple"
                        ),
                    )
                )
        if node.returns is not None and self._is_forbidden_tuple_return(node.returns):
            found.append(
                GuardViolation(
                    path=path,
                    kind="tuple_return",
                    detail=(
                        f"{node.name}: heterogeneous tuple return; "
                        "use a dataclass instead"
                    ),
                )
            )
        return found

    def _iter_annotations(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> list[ast.expr]:
        annotations: list[ast.expr] = []
        for arg in node.args.args + node.args.kwonlyargs:
            if arg.annotation is not None:
                annotations.append(arg.annotation)
        if node.args.vararg is not None and node.args.vararg.annotation is not None:
            annotations.append(node.args.vararg.annotation)
        if node.args.kwarg is not None and node.args.kwarg.annotation is not None:
            annotations.append(node.args.kwarg.annotation)
        if node.returns is not None:
            annotations.append(node.returns)
        return annotations

    def _is_variadic_tuple(self, annotation: ast.expr) -> bool:
        if not isinstance(annotation, ast.Subscript):
            return False
        if not self._is_name(annotation.value, "tuple"):
            return False
        slice_node = annotation.slice
        if isinstance(slice_node, ast.Tuple):
            return any(
                isinstance(element, ast.Constant) and element.value is Ellipsis
                for element in slice_node.elts
            )
        return False

    def _is_forbidden_tuple_return(self, annotation: ast.expr) -> bool:
        if self._is_flask_response_union(annotation):
            return False
        if isinstance(annotation, ast.Subscript) and self._is_name(
            annotation.value, "tuple"
        ):
            return not self._is_variadic_tuple(annotation)
        if isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):
            return self._is_forbidden_tuple_return(
                annotation.left
            ) or self._is_forbidden_tuple_return(annotation.right)
        return False

    def _is_flask_response_union(self, annotation: ast.expr) -> bool:
        if not self._allow_flask_response_tuple:
            return False
        if not isinstance(annotation, ast.BinOp) or not isinstance(
            annotation.op, ast.BitOr
        ):
            return False
        left_ok = self._is_name(annotation.left, "Response")
        right = annotation.right
        if not isinstance(right, ast.Subscript):
            return False
        if not self._is_name(right.value, "tuple"):
            return False
        if not isinstance(right.slice, ast.Tuple) or len(right.slice.elts) != 2:
            return False
        first, second = right.slice.elts
        return self._is_name(first, "Response") and self._is_name(second, "int") and left_ok

    def _is_name(self, node: ast.expr, expected: str) -> bool:
        return isinstance(node, ast.Name) and node.id == expected
