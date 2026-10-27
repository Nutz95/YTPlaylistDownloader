import sys
from pathlib import Path


class YtdlpArgvBuilder:
    """Build shared ``python -m yt_dlp`` argument prefixes (cookies, etc.)."""

    def __init__(
        self,
        cookies_from_browser: str = "",
        cookies_file: str = "",
    ) -> None:
        self._cookies_from_browser = cookies_from_browser.strip()
        self._cookies_file = cookies_file.strip()

    def prefix(self) -> list[str]:
        """Return ``[python, -m, yt_dlp, …optional cookie flags]``."""
        argv = [sys.executable, "-m", "yt_dlp"]
        if self._cookies_file != "":
            argv.extend(["--cookies", str(Path(self._cookies_file))])
        elif self._cookies_from_browser != "":
            argv.extend(
                ["--cookies-from-browser", self._cookies_from_browser]
            )
        return argv
