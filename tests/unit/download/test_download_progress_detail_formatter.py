from ytpd.domain.download_progress_snapshot import DownloadProgressSnapshot
from ytpd.download.download_progress_detail_formatter import (
    DownloadProgressDetailFormatter,
)


def test_formats_downloading_percent() -> None:
    text = DownloadProgressDetailFormatter().format(
        DownloadProgressSnapshot(
            media_key="vid",
            status="downloading",
            percent=12.5,
            downloaded_bytes=1024,
            total_bytes=8192,
            message="x",
        )
    )
    assert "12.5%" in text


def test_formats_waiting_status() -> None:
    text = DownloadProgressDetailFormatter().format(
        DownloadProgressSnapshot(
            media_key="vid",
            status="waiting",
            percent=None,
            downloaded_bytes=None,
            total_bytes=None,
            message="waiting",
        )
    )
    assert "waiting" in text.casefold()
