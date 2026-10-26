from pathlib import Path

DEFAULT_SKIPPED_PARTS = frozenset(
    {"__pycache__", ".venv", "site-packages", "node_modules"}
)


def iter_python_files(
    roots: list[Path],
    *,
    skipped_parts: frozenset[str] | None = None,
    skip_init: bool = True,
    skip_tests: bool = False,
) -> list[Path]:
    """Return sorted ``*.py`` paths under roots, honoring skip filters."""
    parts = skipped_parts or DEFAULT_SKIPPED_PARTS
    found: list[Path] = []
    for root in roots:
        for path in root.rglob("*.py"):
            if any(part in parts for part in path.parts):
                continue
            if skip_init and path.name == "__init__.py":
                continue
            if skip_tests and "tests" in path.parts:
                continue
            found.append(path)
    return sorted(found)


def preceding_lines_contain_marker(
    source_lines: list[str],
    line_number: int,
    marker: str,
    lookback: int = 3,
) -> bool:
    """Return True when ``marker`` appears in the lines above ``line_number``."""
    if line_number <= 0:
        return False
    for offset in range(lookback):
        index = line_number - 1 - offset
        if index < 0:
            continue
        if marker in source_lines[index]:
            return True
    return False
