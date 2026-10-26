from pathlib import Path

from python_guardrails import assert_roots_clean


def test_source_guardrails() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    source_root = repo_root / "src" / "ytpd"
    tests_root = repo_root / "tests"
    assert_roots_clean(
        size_roots=[source_root, tests_root],
        python_roots=[source_root, tests_root],
    )
