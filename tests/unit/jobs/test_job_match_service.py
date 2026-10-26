from dataclasses import replace
from pathlib import Path

from ytpd.domain.match_candidate import MatchCandidate
from ytpd.domain.match_result import MatchResult
from ytpd.domain.match_score import MatchScore
from ytpd.domain.source_kind import SourceKind
from ytpd.domain.track_phase import TrackPhase
from ytpd.domain.track_ref import TrackRef
from ytpd.jobs.job_match_service import JobMatchService
from ytpd.jobs.job_store import JobStore
from ytpd.jobs.sqlite_job_checkpoint_store import SqliteJobCheckpointStore
from ytpd.match.match_pool import MatchPool
from tests.fakes.fake_youtube_matcher import FakeYoutubeMatcher


def test_match_job_persists_partial_results_when_one_track_fails(
    tmp_path: Path,
) -> None:
    store = JobStore(SqliteJobCheckpointStore(tmp_path / "jobs.db"))
    job = store.create("https://www.deezer.com/playlist/1")
    tracks = (
        TrackRef(
            track_id="ok",
            title="Ok",
            artist="A",
            duration_sec=1,
            source_kind=SourceKind.DEEZER_PLAYLIST,
            phase=TrackPhase.RESOLVED,
            youtube_url=None,
            deezer_id="1",
            error_message=None,
        ),
        TrackRef(
            track_id="bad",
            title="Bad",
            artist="B",
            duration_sec=2,
            source_kind=SourceKind.DEEZER_PLAYLIST,
            phase=TrackPhase.RESOLVED,
            youtube_url=None,
            deezer_id="2",
            error_message=None,
        ),
    )
    store.save(replace(job, tracks=tracks))
    matcher = FakeYoutubeMatcher(
        {
            "ok": MatchResult(
                track_id="ok",
                matched=True,
                candidate=MatchCandidate(
                    youtube_url="https://youtu.be/ok",
                    title="Ok",
                    channel="A",
                    duration_sec=1,
                    score=MatchScore(90.0),
                ),
                error_message=None,
            ),
            "bad": MatchResult(
                track_id="bad",
                matched=False,
                candidate=None,
                error_message="simulated search failure",
            ),
        }
    )
    updated = JobMatchService(store, MatchPool(matcher, max_workers=2)).match_job(
        job.job_id
    )
    by_id = {track.track_id: track for track in updated.tracks}
    assert by_id["ok"].phase is TrackPhase.MATCHED
    assert by_id["ok"].youtube_url == "https://youtu.be/ok"
    assert by_id["bad"].phase is TrackPhase.MATCH_FAILED
    assert by_id["bad"].error_message == "simulated search failure"
