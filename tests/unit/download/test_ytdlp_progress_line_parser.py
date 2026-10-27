from ytpd.download.ytdlp_progress_line_parser import YtdlpProgressLineParser


def test_parses_percent_and_size() -> None:
    parsed = YtdlpProgressLineParser().parse(
        "[download]  45.2% of  3.21MiB at  234.56KiB/s ETA 00:15"
    )
    assert parsed is not None
    assert parsed.percent == 45.2
    assert parsed.total_bytes is not None
    assert parsed.downloaded_bytes is not None


def test_ignores_non_progress_lines() -> None:
    assert YtdlpProgressLineParser().parse("[download] Destination: foo.media") is None
