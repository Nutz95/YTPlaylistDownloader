from pathlib import Path

from tests.fakes.fake_ytdlp_flat_playlist_client import FakeYtdlpFlatPlaylistClient
from ytpd.domain.source_kind import SourceKind
from ytpd.domain.track_phase import TrackPhase
from ytpd.resolve.youtube_resolver import YoutubeResolver
from ytpd.resolve.ytdlp_flat_playlist_parser import YtdlpFlatPlaylistParser

_FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"


def test_parser_and_resolver_from_playlist_fixture() -> None:
    fixture = (_FIXTURES / "youtube_playlist_flat.json").read_text(encoding="utf-8")
    entries = YtdlpFlatPlaylistParser().parse(fixture)
    url = "https://www.youtube.com/playlist?list=PLtest"
    client = FakeYtdlpFlatPlaylistClient({url: entries})
    result = YoutubeResolver(client).resolve(url, SourceKind.YOUTUBE_PLAYLIST)
    assert result.source_kind is SourceKind.YOUTUBE_PLAYLIST
    assert len(result.tracks) == 2
    assert result.tracks[0].track_id == "vid1"
    assert result.tracks[0].phase is TrackPhase.MATCHED
    assert result.tracks[0].youtube_url == "https://www.youtube.com/watch?v=vid1"
    assert result.tracks[1].duration_sec == 240


def test_parser_single_video_fixture() -> None:
    fixture = (_FIXTURES / "youtube_video_flat.json").read_text(encoding="utf-8")
    entries = YtdlpFlatPlaylistParser().parse(fixture)
    url = "https://youtu.be/single1"
    result = YoutubeResolver(
        FakeYtdlpFlatPlaylistClient({url: entries}),
    ).resolve(url, SourceKind.YOUTUBE_VIDEO)
    assert result.source_kind is SourceKind.YOUTUBE_VIDEO
    assert len(result.tracks) == 1
    assert result.tracks[0].artist == "Solo Artist"


def test_parser_empty_entries_stays_empty() -> None:
    tracks = YtdlpFlatPlaylistParser().parse(
        '{"id":"PLempty","title":"Empty","entries":[]}'
    )
    assert tracks == []
