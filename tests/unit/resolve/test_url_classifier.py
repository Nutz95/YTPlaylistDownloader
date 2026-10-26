import pytest

from ytpd.domain.source_kind import SourceKind
from ytpd.resolve.unsupported_source_url_error import UnsupportedSourceUrlError
from ytpd.resolve.url_classifier import UrlClassifier


def test_classify_youtube_and_deezer_urls() -> None:
    classifier = UrlClassifier()
    assert (
        classifier.classify("https://www.youtube.com/playlist?list=PLabc")
        is SourceKind.YOUTUBE_PLAYLIST
    )
    assert (
        classifier.classify("https://www.youtube.com/watch?v=abc123")
        is SourceKind.YOUTUBE_VIDEO
    )
    assert classifier.classify("https://youtu.be/abc123") is SourceKind.YOUTUBE_VIDEO
    assert (
        classifier.classify("https://www.deezer.com/playlist/123")
        is SourceKind.DEEZER_PLAYLIST
    )
    assert (
        classifier.classify("https://link.deezer.com/s/abc")
        is SourceKind.DEEZER_PLAYLIST
    )


def test_classify_rejects_unknown_host() -> None:
    with pytest.raises(UnsupportedSourceUrlError):
        UrlClassifier().classify("https://example.test/list")
