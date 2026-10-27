from ytpd.runtime.ytpd_server_command_matcher import YtpdServerCommandMatcher


def test_matches_python_module_ytpd() -> None:
    matcher = YtpdServerCommandMatcher()
    assert matcher.matches(
        r'E:\venv\Scripts\python.exe -m ytpd'
    )
    assert matcher.matches(
        r'"E:\venv\Scripts\python.exe" -m ytpd'
    )


def test_ignores_yt_dlp_children() -> None:
    matcher = YtpdServerCommandMatcher()
    assert matcher.matches(
        r"python.exe -m yt_dlp --cookies x https://youtu.be/a"
    ) is False


def test_matches_console_script() -> None:
    matcher = YtpdServerCommandMatcher()
    assert matcher.matches(r"E:\venv\Scripts\ytpd.exe")
