from pathlib import Path

from ytpd.resolve.ytdlp_video_metadata_parser import YtdlpVideoMetadataParser

_FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"


def test_parser_reads_chapters_from_fixture() -> None:
    text = (_FIXTURES / "youtube_video_chapters.json").read_text(encoding="utf-8")
    metadata = YtdlpVideoMetadataParser().parse(text)
    assert metadata.video_id == "2UznMNQQ0H8"
    assert metadata.uploader == "KageYume"
    assert len(metadata.chapters) == 3
    assert metadata.chapters[0].title == "Metamorphosis umbrae"
    assert metadata.chapters[0].start_sec == 0.0
    assert metadata.chapters[1].end_sec == 233.0


def test_parser_without_chapters_returns_empty_list() -> None:
    metadata = YtdlpVideoMetadataParser().parse(
        '{"id":"v1","title":"Solo","uploader":"A","duration":10,'
        '"webpage_url":"https://youtu.be/v1"}'
    )
    assert metadata.chapters == []
    assert metadata.duration_sec == 10
