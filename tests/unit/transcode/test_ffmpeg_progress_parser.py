from ytpd.transcode.ffmpeg_progress_parser import FfmpegProgressParser


def test_parses_out_time_ms() -> None:
    assert FfmpegProgressParser().elapsed_sec("out_time_ms=1500000") == 1.5


def test_parses_out_time_hms() -> None:
    assert FfmpegProgressParser().elapsed_sec("out_time=00:01:30.5") == 90.5


def test_detects_progress_end() -> None:
    assert FfmpegProgressParser().is_end("progress=end") is True
    assert FfmpegProgressParser().is_end("out_time_ms=1") is False
