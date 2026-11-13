import re
from pathlib import Path


_KEY_PATTERN = re.compile(r'"([a-z0-9_.]+)":')


def _catalog_keys(path: Path) -> set[str]:
    return set(_KEY_PATTERN.findall(path.read_text(encoding="utf-8")))


def test_en_and_fr_i18n_catalogs_share_the_same_keys() -> None:
    js_dir = (
        Path(__file__).resolve().parents[3]
        / "src"
        / "ytpd"
        / "web"
        / "static"
        / "js"
    )
    en_keys = _catalog_keys(js_dir / "i18n_messages_en.js")
    fr_keys = _catalog_keys(js_dir / "i18n_messages_fr.js")
    assert en_keys
    assert en_keys == fr_keys
