from ytpd.domain.source_kind import SourceKind
from ytpd.domain.track_phase import TrackPhase
from ytpd.domain.track_ref import TrackRef
from ytpd.domain.ytdlp_flat_entry import YtdlpFlatEntry
from ytpd.match.static_match_scorer import StaticMatchScorer
from ytpd.match.static_youtube_matcher import StaticYoutubeMatcher
from tests.fakes.fake_youtube_search_client import FakeYoutubeSearchClient
from tests.fakes.raising_youtube_search_client import RaisingYoutubeSearchClient


def test_static_matcher_picks_best_scored_hit() -> None:
    track = TrackRef(
        track_id="t1",
        title="Stupid Girl",
        artist="Garbage",
        duration_sec=257,
        source_kind=SourceKind.DEEZER_PLAYLIST,
        phase=TrackPhase.RESOLVED,
        youtube_url=None,
        deezer_id="1",
        error_message=None,
    )
    client = FakeYoutubeSearchClient(
        {
            "Garbage Stupid Girl": [
                YtdlpFlatEntry(
                    video_id="bad",
                    title="Random Song",
                    uploader="Someone",
                    duration_sec=100,
                    webpage_url="https://youtu.be/bad",
                ),
                YtdlpFlatEntry(
                    video_id="good",
                    title="Stupid Girl",
                    uploader="Garbage",
                    duration_sec=255,
                    webpage_url="https://youtu.be/good",
                ),
            ]
        }
    )
    result = StaticYoutubeMatcher(client, StaticMatchScorer()).match(track)
    assert result.matched is True
    assert result.candidate is not None
    assert result.candidate.youtube_url == "https://youtu.be/good"


def test_static_matcher_isolates_search_probe_errors() -> None:
    track = TrackRef(
        track_id="t2",
        title="Song",
        artist="Artist",
        duration_sec=200,
        source_kind=SourceKind.DEEZER_PLAYLIST,
        phase=TrackPhase.RESOLVED,
        youtube_url=None,
        deezer_id="2",
        error_message=None,
    )
    client = RaisingYoutubeSearchClient({}, {"Artist Song"})
    result = StaticYoutubeMatcher(client, StaticMatchScorer()).match(track)
    assert result.matched is False
    assert result.error_message == "simulated search failure"
