from ytpd.domain.source_kind import SourceKind
from ytpd.domain.track_phase import TrackPhase
from ytpd.domain.track_ref import TrackRef
from ytpd.domain.ytdlp_flat_entry import YtdlpFlatEntry
from ytpd.lmstudio.http_lm_studio_client import HttpLmStudioClient
from ytpd.lmstudio.lm_studio_settings import LmStudioSettings
from ytpd.match.cascading_youtube_matcher import CascadingYoutubeMatcher
from ytpd.match.static_match_decider import StaticMatchDecider
from ytpd.match.static_match_scorer import StaticMatchScorer
from ytpd.match.youtube_candidate_fetcher import YoutubeCandidateFetcher
from tests.fakes.counting_youtube_search_client import CountingYoutubeSearchClient
from tests.fakes.fake_lm_studio_http_transport import FakeLmStudioHttpTransport
from tests.fakes.fake_resource_gate import FakeResourceGate
from tests.fakes.fake_youtube_search_client import FakeYoutubeSearchClient


def _weak_hit_track() -> TrackRef:
    return TrackRef(
        track_id="t1",
        title="Obscure",
        artist="Nobody",
        duration_sec=200,
        source_kind=SourceKind.DEEZER_PLAYLIST,
        phase=TrackPhase.RESOLVED,
        youtube_url=None,
        deezer_id="1",
        error_message=None,
    )


def test_cascade_searches_once_then_uses_llm() -> None:
    settings = LmStudioSettings(
        base_url="http://127.0.0.1:1234/v1",
        model="test-model",
        timeout_sec=1.0,
    )
    inner = FakeYoutubeSearchClient(
        {
            "Nobody Obscure": [
                YtdlpFlatEntry(
                    video_id="x",
                    title="Unrelated Clip",
                    uploader="Other",
                    duration_sec=10,
                    webpage_url="https://youtu.be/x",
                )
            ]
        }
    )
    search = CountingYoutubeSearchClient(inner)
    transport = FakeLmStudioHttpTransport(["test-model"], ["0"])
    gate = FakeResourceGate()
    matcher = CascadingYoutubeMatcher(
        YoutubeCandidateFetcher(search, StaticMatchScorer()),
        StaticMatchDecider(),
        HttpLmStudioClient(transport, settings),
        gate,
    )
    result = matcher.match(_weak_hit_track())
    assert search.search_calls == 1
    assert transport.chat_calls == 1
    assert gate.llm_acquire_count == 1
    assert result.matched is True
    assert result.candidate is not None
    assert result.candidate.youtube_url == "https://youtu.be/x"


def test_cascade_reports_offline_lm_studio() -> None:
    settings = LmStudioSettings(
        base_url="http://127.0.0.1:1234/v1",
        model="test-model",
        timeout_sec=1.0,
    )
    search = FakeYoutubeSearchClient(
        {
            "Nobody Obscure": [
                YtdlpFlatEntry(
                    video_id="x",
                    title="Unrelated Clip",
                    uploader="Other",
                    duration_sec=10,
                    webpage_url="https://youtu.be/x",
                )
            ]
        }
    )
    matcher = CascadingYoutubeMatcher(
        YoutubeCandidateFetcher(search, StaticMatchScorer()),
        StaticMatchDecider(),
        HttpLmStudioClient(
            FakeLmStudioHttpTransport(["test-model"], [], offline=True),
            settings,
        ),
        FakeResourceGate(),
    )
    result = matcher.match(_weak_hit_track())
    assert result.matched is False
    assert result.error_message == "LM Studio est hors ligne ou injoignable."
