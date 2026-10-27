from ytpd.jobs.mp3_filename_sanitizer import Mp3FilenameSanitizer


def test_stem_for_track_uses_artist_and_title() -> None:
    stem = Mp3FilenameSanitizer().stem_for_track(
        "Imagine Dragons",
        "Radioactive",
        "deezer-63510358",
    )
    assert stem == "Imagine Dragons - Radioactive"


def test_stem_strips_invalid_windows_chars() -> None:
    stem = Mp3FilenameSanitizer().stem_for_track(
        'AC/DC',
        'Thunder:struck?',
        "id",
    )
    assert "/" not in stem
    assert ":" not in stem
    assert "?" not in stem
    assert stem == "AC DC - Thunder struck"


def test_stem_falls_back_to_id_when_empty() -> None:
    assert (
        Mp3FilenameSanitizer().stem_for_track("  ", "", "deezer-1") == "deezer-1"
    )
