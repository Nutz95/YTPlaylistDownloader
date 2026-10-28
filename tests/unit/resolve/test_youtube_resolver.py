from pathlib import Path

from tests.fakes.fake_ytdlp_flat_playlist_client import FakeYtdlpFlatPlaylistClient
from tests.fakes.fake_ytdlp_video_metadata_client import FakeYtdlpVideoMetadataClient
from ytpd.domain.source_kind import SourceKind
from ytpd.domain.track_phase import TrackPhase
from ytpd.domain.ytdlp_video_metadata import YtdlpVideoMetadata
from ytpd.resolve.youtube_resolver import YoutubeResolver
from ytpd.resolve.ytdlp_flat_playlist_parser import YtdlpFlatPlaylistParser
from ytpd.resolve.ytdlp_video_metadata_parser import YtdlpVideoMetadataParser

_FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"


def test_parser_and_resolver_from_playlist_fixture() -> None:
    fixture = (_FIXTURES / "youtube_playlist_flat.json").read_text(encoding="utf-8")
    parsed = YtdlpFlatPlaylistParser().parse(fixture)
    url = "https://www.youtube.com/playlist?list=PLtest"
    client = FakeYtdlpFlatPlaylistClient(
        {url: parsed.entries},
        titles_by_url={url: parsed.title or ""},
    )
    result = YoutubeResolver(
        client,
        FakeYtdlpVideoMetadataClient({}),
    ).resolve(url, SourceKind.YOUTUBE_PLAYLIST)
    assert result.source_kind is SourceKind.YOUTUBE_PLAYLIST
    assert result.source_title == "Demo playlist"
    assert len(result.tracks) == 2
    assert result.tracks[0].track_id == "vid1"
    assert result.tracks[0].phase is TrackPhase.MATCHED
    assert result.tracks[0].youtube_url == "https://www.youtube.com/watch?v=vid1"
    assert result.tracks[1].duration_sec == 240


def test_resolver_expands_chaptered_video() -> None:
    text = (_FIXTURES / "youtube_video_chapters.json").read_text(encoding="utf-8")
    metadata = YtdlpVideoMetadataParser().parse(text)
    url = "https://youtu.be/2UznMNQQ0H8"
    result = YoutubeResolver(
        FakeYtdlpFlatPlaylistClient({}),
        FakeYtdlpVideoMetadataClient({url: metadata}),
    ).resolve(url, SourceKind.YOUTUBE_VIDEO)
    assert len(result.tracks) == 3
    assert result.source_title == metadata.title
    assert result.tracks[0].track_id == "2UznMNQQ0H8__ch00"
    assert result.tracks[0].title == "Metamorphosis umbrae"
    assert result.tracks[0].artist == "KageYume"
    assert result.tracks[0].chapter_start_sec == 0.0
    assert result.tracks[0].chapter_end_sec == 138.0
    assert result.tracks[0].parent_video_id == "2UznMNQQ0H8"
    assert result.tracks[0].chapter_index == 0
    assert result.tracks[0].phase is TrackPhase.MATCHED
    assert result.tracks[2].track_id == "2UznMNQQ0H8__ch02"


def test_resolver_single_video_without_chapters() -> None:
    url = "https://youtu.be/single1"
    metadata = YtdlpVideoMetadata(
        video_id="single1",
        title="Single Video",
        uploader="Solo Artist",
        duration_sec=95,
        webpage_url="https://www.youtube.com/watch?v=single1",
        chapters=[],
    )
    result = YoutubeResolver(
        FakeYtdlpFlatPlaylistClient({}),
        FakeYtdlpVideoMetadataClient({url: metadata}),
    ).resolve(url, SourceKind.YOUTUBE_VIDEO)
    assert len(result.tracks) == 1
    assert result.source_title == "Single Video"
    assert result.tracks[0].track_id == "single1"
    assert result.tracks[0].artist == "Solo Artist"
    assert result.tracks[0].parent_video_id is None


def test_parser_empty_entries_stays_empty() -> None:
    parsed = YtdlpFlatPlaylistParser().parse(
        '{"id":"PLempty","title":"Empty","entries":[]}'
    )
    assert parsed.title == "Empty"
    assert parsed.entries == []
