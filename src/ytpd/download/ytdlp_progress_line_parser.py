import re

from ytpd.domain.ytdlp_progress_parse_result import YtdlpProgressParseResult

_PERCENT = re.compile(r"\[download\]\s+(\d+(?:\.\d+)?)%")
_OF_TOTAL = re.compile(
    r"\[download\]\s+(\d+(?:\.\d+)?)%\s+of\s+~?\s*([\d.]+)([KMG]?i?B)",
    re.IGNORECASE,
)
_UNIT_MULTIPLIER = {
    "B": 1.0,
    "KB": 1024.0,
    "KIB": 1024.0,
    "MB": 1024.0 ** 2,
    "MIB": 1024.0 ** 2,
    "GB": 1024.0 ** 3,
    "GIB": 1024.0 ** 3,
}


class YtdlpProgressLineParser:
    """Parse yt-dlp ``[download]`` progress lines into percent/bytes."""

    def parse(self, line: str) -> YtdlpProgressParseResult | None:
        """Return progress fields when ``line`` is a download percent update."""
        percent_match = _PERCENT.search(line)
        if percent_match is None:
            return None
        percent = float(percent_match.group(1))
        downloaded_bytes: int | None = None
        total_bytes: int | None = None
        of_match = _OF_TOTAL.search(line)
        if of_match is not None:
            percent = float(of_match.group(1))
            total_bytes = self._to_bytes(float(of_match.group(2)), of_match.group(3))
            if total_bytes is not None:
                downloaded_bytes = int(total_bytes * (percent / 100.0))
        return YtdlpProgressParseResult(
            percent=percent,
            downloaded_bytes=downloaded_bytes,
            total_bytes=total_bytes,
            message=line.strip(),
        )

    def _to_bytes(self, value: float, unit: str) -> int | None:
        multiplier = _UNIT_MULTIPLIER.get(unit.upper())
        if multiplier is None:
            return None
        return int(value * multiplier)
