from ytpd.domain.transcode_progress_snapshot import TranscodeProgressSnapshot
from ytpd.transcode.transcode_progress_detail_formatter import (
    TranscodeProgressDetailFormatter,
)


def test_format_includes_backend_and_percent() -> None:
    text = TranscodeProgressDetailFormatter().format(
        TranscodeProgressSnapshot(
            track_id="t1",
            status="encoding",
            backend_label="CPU",
            percent=42.0,
            message="t=12.0s",
        )
    )
    assert text == "CPU · 42%"


def test_format_starting() -> None:
    text = TranscodeProgressDetailFormatter().format(
        TranscodeProgressSnapshot(
            track_id="t1",
            status="starting",
            backend_label="CPU",
            percent=None,
            message="starting ffmpeg",
        )
    )
    assert "CPU" in text
    assert "starting" in text
