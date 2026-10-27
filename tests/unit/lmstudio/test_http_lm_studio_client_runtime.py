from tests.fakes.fake_lm_studio_http_transport import FakeLmStudioHttpTransport
from tests.fakes.fake_lm_studio_model_runtime import FakeLmStudioModelRuntime
from ytpd.domain.match_candidate import MatchCandidate
from ytpd.domain.match_score import MatchScore
from ytpd.domain.source_kind import SourceKind
from ytpd.domain.track_phase import TrackPhase
from ytpd.domain.track_ref import TrackRef
from ytpd.lmstudio.http_lm_studio_client import HttpLmStudioClient
from ytpd.lmstudio.lm_studio_settings import LmStudioSettings


def test_choose_match_ensures_runtime_before_chat() -> None:
    runtime = FakeLmStudioModelRuntime()
    transport = FakeLmStudioHttpTransport(
        ["test-model"],
        [
            '{"candidate_index": 0, "reason": "ok"}',
            '{"candidate_index": 0, "reason": "ok"}',
        ],
    )
    client = HttpLmStudioClient(
        transport,
        LmStudioSettings(
            base_url="http://127.0.0.1:1234/v1",
            model="test-model",
            timeout_sec=1.0,
            context_length=8192,
        ),
        runtime,
    )
    track = TrackRef(
        track_id="t1",
        title="Song",
        artist="Artist",
        duration_sec=180,
        source_kind=SourceKind.DEEZER_PLAYLIST,
        phase=TrackPhase.RESOLVED,
        youtube_url=None,
        deezer_id="1",
        error_message=None,
    )
    candidate = MatchCandidate(
        youtube_url="https://youtu.be/x",
        title="Song",
        channel="Artist",
        duration_sec=180,
        score=MatchScore(50.0),
    )
    choice = client.choose_match(track, [candidate])
    assert runtime.ensure_ready_calls == 1
    assert choice.candidate_index == 0
    client.choose_match(track, [candidate])
    assert runtime.ensure_ready_calls == 1


def test_choose_match_includes_rejection_context_in_prompt() -> None:
    transport = FakeLmStudioHttpTransport(
        ["test-model"],
        ['{"candidate_index": 0, "reason": "ok"}'],
    )
    client = HttpLmStudioClient(
        transport,
        LmStudioSettings(
            base_url="http://127.0.0.1:1234/v1",
            model="test-model",
            timeout_sec=1.0,
            context_length=8192,
        ),
        FakeLmStudioModelRuntime(),
    )
    track = TrackRef(
        track_id="t1",
        title="Song",
        artist="Artist",
        duration_sec=180,
        source_kind=SourceKind.DEEZER_PLAYLIST,
        phase=TrackPhase.RESOLVED,
        youtube_url=None,
        deezer_id="1",
        error_message=None,
    )
    candidate = MatchCandidate(
        youtube_url="https://youtu.be/x",
        title="Song",
        channel="Artist",
        duration_sec=180,
        score=MatchScore(50.0),
    )
    client.choose_match(
        track,
        [candidate],
        rejection_context="Wrong Cover (https://youtu.be/bad): duration mismatch",
    )
    assert len(transport.user_prompts) == 1
    prompt = transport.user_prompts[0]
    assert "Previously rejected because:" in prompt
    assert "duration mismatch" in prompt
