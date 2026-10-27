import sys
from pathlib import Path

from ytpd.resolve.ytdlp_argv_builder import YtdlpArgvBuilder


def test_prefix_without_cookies_is_python_module_only() -> None:
    argv = YtdlpArgvBuilder("").prefix()
    assert argv == [sys.executable, "-m", "yt_dlp"]


def test_prefix_includes_cookies_from_browser_when_set() -> None:
    argv = YtdlpArgvBuilder("chrome").prefix()
    assert argv[:3] == [sys.executable, "-m", "yt_dlp"]
    assert argv[3:] == ["--cookies-from-browser", "chrome"]


def test_prefix_strips_whitespace_cookies() -> None:
    assert YtdlpArgvBuilder("  ").prefix() == [sys.executable, "-m", "yt_dlp"]
    assert "--cookies-from-browser" in YtdlpArgvBuilder(" edge ").prefix()


def test_cookies_file_takes_priority_over_browser() -> None:
    argv = YtdlpArgvBuilder("brave", "config/youtube_cookies.txt").prefix()
    assert "--cookies-from-browser" not in argv
    assert argv[3] == "--cookies"
    assert Path(argv[4]) == Path("config/youtube_cookies.txt")


def test_cookies_file_alone() -> None:
    argv = YtdlpArgvBuilder("", "cookies.txt").prefix()
    assert argv[3] == "--cookies"
    assert Path(argv[4]) == Path("cookies.txt")
