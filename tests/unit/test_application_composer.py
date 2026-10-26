from ytpd.application_composer import ApplicationComposer


def test_composer_builds_app_and_settings() -> None:
    composed = ApplicationComposer().compose()
    assert composed.settings.host == "127.0.0.1"
    assert composed.settings.port == 8765
    assert composed.app.title == "YTPlaylistDownloader"
