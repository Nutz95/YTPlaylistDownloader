from pathlib import Path

from python_guardrails.baseline_store import assert_within_baseline
from python_guardrails.dynamic_access_guard import DynamicAccessGuard
from python_guardrails.file_size_guard import FileSizeGuard
from python_guardrails.function_line_limit_guard import FunctionLineLimitGuard
from python_guardrails.guard_violation import GuardViolation
from python_guardrails.inline_fake_class_guard import InlineFakeClassGuard
from python_guardrails.monkeypatch_setattr_guard import MonkeypatchSetattrGuard
from python_guardrails.nested_function_def_guard import NestedFunctionDefGuard
from python_guardrails.owned_positional_tuple_guard import OwnedPositionalTupleGuard
from python_guardrails.public_docstring_guard import PublicDocstringGuard
from python_guardrails.python_structure_guard import PythonStructureGuard
from python_guardrails.python_typing_guard import PythonTypingGuard


def check_roots(
    size_roots: list[Path],
    python_roots: list[Path] | None = None,
    *,
    check_size: bool = True,
    check_structure: bool = True,
    check_typing: bool = True,
    check_dynamic_access: bool = True,
    check_nested_defs: bool = True,
    check_function_lines: bool = True,
    check_owned_tuples: bool = True,
    check_inline_fakes: bool = True,
    check_monkeypatch: bool = True,
    check_public_docstrings: bool = True,
) -> list[GuardViolation]:
    """Run the standard SOLID guardrail set on the given roots."""
    py_roots = python_roots if python_roots is not None else size_roots
    violations: list[GuardViolation] = []
    if check_size:
        violations.extend(FileSizeGuard().check(size_roots))
    if check_structure:
        violations.extend(PythonStructureGuard().check(py_roots))
    if check_typing:
        violations.extend(PythonTypingGuard().check(py_roots))
    if check_dynamic_access:
        violations.extend(DynamicAccessGuard().check(py_roots))
    if check_nested_defs:
        violations.extend(NestedFunctionDefGuard().check(py_roots))
    if check_function_lines:
        violations.extend(FunctionLineLimitGuard().check(py_roots))
    if check_owned_tuples:
        violations.extend(OwnedPositionalTupleGuard().check(py_roots))
    if check_inline_fakes:
        violations.extend(InlineFakeClassGuard().check(py_roots))
    if check_monkeypatch:
        violations.extend(MonkeypatchSetattrGuard().check(py_roots))
    if check_public_docstrings:
        violations.extend(PublicDocstringGuard().check(py_roots))
    return violations


def format_violations(violations: list[GuardViolation]) -> str:
    """Format violations as a multi-line bullet list for assertion messages."""
    return "\n".join(
        f"- {item.path}: {item.kind} ({item.detail})" for item in violations
    )


def assert_roots_clean(
    size_roots: list[Path],
    python_roots: list[Path] | None = None,
    *,
    check_size: bool = True,
    check_structure: bool = True,
    check_typing: bool = True,
    check_dynamic_access: bool = True,
    check_nested_defs: bool = True,
    check_function_lines: bool = True,
    check_owned_tuples: bool = True,
    check_inline_fakes: bool = True,
    check_monkeypatch: bool = True,
    check_public_docstrings: bool = True,
) -> None:
    """Raise AssertionError when any enabled guardrail reports a violation."""
    violations = check_roots(
        size_roots,
        python_roots,
        check_size=check_size,
        check_structure=check_structure,
        check_typing=check_typing,
        check_dynamic_access=check_dynamic_access,
        check_nested_defs=check_nested_defs,
        check_function_lines=check_function_lines,
        check_owned_tuples=check_owned_tuples,
        check_inline_fakes=check_inline_fakes,
        check_monkeypatch=check_monkeypatch,
        check_public_docstrings=check_public_docstrings,
    )
    if violations:
        raise AssertionError(
            "Guardrail violations:\n" + format_violations(violations)
        )


def assert_roots_within_baseline(
    size_roots: list[Path],
    baseline_path: Path,
    python_roots: list[Path] | None = None,
    *,
    update_baseline: bool = False,
    check_size: bool = True,
    check_structure: bool = True,
    check_typing: bool = True,
    check_dynamic_access: bool = True,
    check_nested_defs: bool = True,
    check_function_lines: bool = True,
    check_owned_tuples: bool = True,
    check_inline_fakes: bool = True,
    check_monkeypatch: bool = True,
    check_public_docstrings: bool = True,
) -> None:
    """Progressive ratchet: counts per kind must not exceed baseline JSON."""
    violations = check_roots(
        size_roots,
        python_roots,
        check_size=check_size,
        check_structure=check_structure,
        check_typing=check_typing,
        check_dynamic_access=check_dynamic_access,
        check_nested_defs=check_nested_defs,
        check_function_lines=check_function_lines,
        check_owned_tuples=check_owned_tuples,
        check_inline_fakes=check_inline_fakes,
        check_monkeypatch=check_monkeypatch,
        check_public_docstrings=check_public_docstrings,
    )
    assert_within_baseline(
        violations,
        baseline_path,
        update=update_baseline,
    )
