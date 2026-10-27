from ytpd.domain.source_kind import SourceKind
from ytpd.domain.track_phase import TrackPhase
from ytpd.domain.track_ref import TrackRef
from ytpd.domain.ytdlp_flat_entry import YtdlpFlatEntry
from ytpd.match.static_match_scorer import StaticMatchScorer
from ytpd.match.youtube_candidate_fetcher import YoutubeCandidateFetcher
from tests.fakes.fake_youtube_search_client import FakeYoutubeSearchClient


def test_fetcher_retries_fallback_when_primary_empty() -> None:
    track = TrackRef(
        track_id="t1",
        title="Libertine",
        artist="Mylène Farmer",
        duration_sec=200,
        source_kind=SourceKind.DEEZER_PLAYLIST,
        phase=TrackPhase.RESOLVED,
        youtube_url=None,
        deezer_id="1",
        error_message=None,
    )
    hit = YtdlpFlatEntry(
        video_id="x",
        title="Mylène Farmer - Libertine",
        uploader="Mylène Farmer",
        duration_sec=200,
        webpage_url="https://youtu.be/x",
    )
    client = FakeYoutubeSearchClient(
        {
            "Mylène Farmer Libertine": [],
            "Mylene Farmer Libertine": [],
            "Mylene Farmer Libertine lyrics": [hit],
        }
    )
    candidates = YoutubeCandidateFetcher(client, StaticMatchScorer()).fetch(track)
    assert len(candidates) == 1
    assert candidates[0].youtube_url == "https://youtu.be/x"


def test_fetcher_strips_feat_in_primary_query() -> None:
    track = TrackRef(
        track_id="t2",
        title="God Gave Me Feet For Dancing (feat. Yazmin Lacey)",
        artist="Ezra Collective",
        duration_sec=210,
        source_kind=SourceKind.DEEZER_PLAYLIST,
        phase=TrackPhase.RESOLVED,
        youtube_url=None,
        deezer_id="2",
        error_message=None,
    )
    hit = YtdlpFlatEntry(
        video_id="y",
        title="Ezra Collective - God Gave Me Feet For Dancing",
        uploader="Ezra Collective",
        duration_sec=210,
        webpage_url="https://youtu.be/y",
    )
    client = FakeYoutubeSearchClient(
        {
            "Ezra Collective God Gave Me Feet For Dancing": [hit],
        }
    )
    candidates = YoutubeCandidateFetcher(client, StaticMatchScorer()).fetch(track)
    assert len(candidates) == 1
    assert candidates[0].youtube_url == "https://youtu.be/y"


def test_fetcher_retry_excluding_skips_rejected_urls() -> None:
    track = TrackRef(
        track_id="t3",
        title="Obscure",
        artist="Nobody",
        duration_sec=200,
        source_kind=SourceKind.DEEZER_PLAYLIST,
        phase=TrackPhase.RESOLVED,
        youtube_url=None,
        deezer_id="3",
        error_message=None,
    )
    rejected = YtdlpFlatEntry(
        video_id="bad",
        title="Wrong",
        uploader="Other",
        duration_sec=10,
        webpage_url="https://youtu.be/bad",
    )
    kept = YtdlpFlatEntry(
        video_id="good",
        title="Nobody Obscure Official",
        uploader="Nobody",
        duration_sec=200,
        webpage_url="https://youtu.be/good",
    )
    client = FakeYoutubeSearchClient(
        {
            "Nobody Obscure official audio": [rejected, kept],
        }
    )
    candidates = YoutubeCandidateFetcher(client, StaticMatchScorer()).fetch_retry_excluding(
        track,
        {"https://youtu.be/bad"},
    )
    assert len(candidates) == 1
    assert candidates[0].youtube_url == "https://youtu.be/good"
