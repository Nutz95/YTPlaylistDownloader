from ytpd.domain.match_candidate import MatchCandidate
from ytpd.domain.match_result import MatchResult
from ytpd.domain.match_score import MatchScore
from ytpd.domain.source_kind import SourceKind
from ytpd.domain.track_phase import TrackPhase
from ytpd.domain.track_ref import TrackRef
from ytpd.jobs.job_cancel_flag import JobCancelFlag
from ytpd.match.match_pool import MatchPool
from tests.fakes.fake_youtube_matcher import FakeYoutubeMatcher


def test_pool_matches_pending_tracks_in_parallel_order_stable() -> None:
    tracks = [
        TrackRef(
            track_id="a",
            title="A",
            artist="X",
            duration_sec=1,
            source_kind=SourceKind.DEEZER_PLAYLIST,
            phase=TrackPhase.RESOLVED,
            youtube_url=None,
            deezer_id="1",
            error_message=None,
        ),
        TrackRef(
            track_id="b",
            title="B",
            artist="Y",
            duration_sec=2,
            source_kind=SourceKind.DEEZER_PLAYLIST,
            phase=TrackPhase.MATCHED,
            youtube_url="https://youtu.be/b",
            deezer_id="2",
            error_message=None,
        ),
        TrackRef(
            track_id="c",
            title="C",
            artist="Z",
            duration_sec=3,
            source_kind=SourceKind.DEEZER_PLAYLIST,
            phase=TrackPhase.RESOLVED,
            youtube_url=None,
            deezer_id="3",
            error_message=None,
        ),
    ]
    matcher = FakeYoutubeMatcher(
        {
            "a": MatchResult(
                track_id="a",
                matched=True,
                candidate=MatchCandidate(
                    youtube_url="https://youtu.be/a",
                    title="A",
                    channel="X",
                    duration_sec=1,
                    score=MatchScore(90.0),
                ),
                error_message=None,
            ),
            "c": MatchResult(
                track_id="c",
                matched=False,
                candidate=None,
                error_message="no hit",
            ),
        }
    )
    results = MatchPool(matcher, max_workers=4, cancel_flag=JobCancelFlag()).run(tracks)
    assert [item.track_id for item in results] == ["a", "c"]
    assert set(matcher.calls) == {"a", "c"}
