from ytpd.download.ytdlp_download_error_hint import YtdlpDownloadErrorHint


def test_dpapi_failure_appends_cookies_file_hint() -> None:
    detail = "ERROR: Failed to decrypt with DPAPI"
    enriched = YtdlpDownloadErrorHint().enrich(detail)
    assert "DPAPI" in enriched
    assert "youtube_cookies_file" in enriched
    assert "Brave" in enriched


def test_non_dpapi_failure_unchanged() -> None:
    detail = "HTTP Error 403: Forbidden"
    assert YtdlpDownloadErrorHint().enrich(detail) == detail
