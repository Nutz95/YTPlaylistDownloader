from ytpd.domain.resume_action import ResumeAction
from ytpd.domain.source_kind import SourceKind
from ytpd.domain.track_artifact_flags import TrackArtifactFlags
from ytpd.domain.track_phase import TrackPhase
from ytpd.domain.track_ref import TrackRef
from ytpd.jobs.track_state_machine import TrackStateMachine


def _track(
    phase: TrackPhase,
    youtube_url: str | None,
) -> TrackRef:
    return TrackRef(
        track_id="t1",
        title="Song",
        artist="Artist",
        duration_sec=120,
        source_kind=SourceKind.DEEZER_PLAYLIST,
        phase=phase,
        youtube_url=youtube_url,
        deezer_id="dz1",
        error_message=None,
    )


def test_resume_decision_table() -> None:
    machine = TrackStateMachine()
    cases: list[tuple[TrackPhase, str | None, TrackArtifactFlags, ResumeAction]] = [
        (
            TrackPhase.DONE,
            "https://youtu.be/a",
            TrackArtifactFlags(True, True),
            ResumeAction.NONE,
        ),
        (
            TrackPhase.SKIPPED,
            None,
            TrackArtifactFlags(False, False),
            ResumeAction.NONE,
        ),
        (
            TrackPhase.RESOLVED,
            None,
            TrackArtifactFlags(False, False),
            ResumeAction.MATCH,
        ),
        (
            TrackPhase.MATCHED,
            "https://youtu.be/a",
            TrackArtifactFlags(False, False),
            ResumeAction.DOWNLOAD,
        ),
        (
            TrackPhase.DOWNLOADED,
            "https://youtu.be/a",
            TrackArtifactFlags(True, False),
            ResumeAction.TRANSCODE,
        ),
        (
            TrackPhase.TRANSCODING,
            "https://youtu.be/a",
            TrackArtifactFlags(True, True),
            ResumeAction.NONE,
        ),
    ]
    for phase, url, flags, expected in cases:
        assert machine.decide(_track(phase, url), flags) is expected
