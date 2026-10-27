from dataclasses import replace
from pathlib import Path

import pytest

from ytpd.domain.job_status import JobStatus
from ytpd.domain.source_kind import SourceKind
from ytpd.domain.track_phase import TrackPhase
from ytpd.domain.track_ref import TrackRef
from ytpd.jobs.invalid_job_error import InvalidJobError
from ytpd.jobs.job_store import JobStore
from ytpd.jobs.job_track_youtube_override_service import (
    JobTrackYoutubeOverrideService,
)
from ytpd.jobs.sqlite_job_checkpoint_store import SqliteJobCheckpointStore


def _failed_track(phase: TrackPhase = TrackPhase.ERROR) -> TrackRef:
    return TrackRef(
        track_id="t1",
        title="Lose Yourself to Dance",
        artist="Daft Punk",
        duration_sec=300,
        source_kind=SourceKind.DEEZER_PLAYLIST,
        phase=phase,
        youtube_url="https://www.youtube.com/watch?v=Q3Bp1QVVieM",
        deezer_id="1",
        error_message="Q3Bp1QVVieM: This video is not available",
    )


def test_override_sets_matched_phase_and_clears_error(tmp_path: Path) -> None:
    store = JobStore(SqliteJobCheckpointStore(tmp_path / "jobs.db"))
    job = store.create("https://example.test/list")
    store.save(replace(job, status=JobStatus.CANCELLED, tracks=[_failed_track()]))
    updated = JobTrackYoutubeOverrideService(store).apply(
        job.job_id,
        "t1",
        "https://youtu.be/NF-kLy44Hls",
    )
    assert updated.status is JobStatus.INTERRUPTED
    track = updated.tracks[0]
    assert track.phase is TrackPhase.MATCHED
    assert track.youtube_url == "https://www.youtube.com/watch?v=NF-kLy44Hls"
    assert track.error_message is None


def test_override_rejects_invalid_youtube_url(tmp_path: Path) -> None:
    store = JobStore(SqliteJobCheckpointStore(tmp_path / "jobs.db"))
    job = store.create("https://example.test/list")
    store.save(
        replace(
            job,
            status=JobStatus.CANCELLED,
            tracks=[_failed_track(TrackPhase.MATCH_FAILED)],
        )
    )
    with pytest.raises(InvalidJobError, match="youtube_url"):
        JobTrackYoutubeOverrideService(store).apply(
            job.job_id,
            "t1",
            "https://example.test/not-youtube",
        )


def test_override_rejects_running_job(tmp_path: Path) -> None:
    store = JobStore(SqliteJobCheckpointStore(tmp_path / "jobs.db"))
    job = store.create("https://example.test/list")
    store.save(replace(job, status=JobStatus.RUNNING, tracks=[_failed_track()]))
    with pytest.raises(InvalidJobError, match="running"):
        JobTrackYoutubeOverrideService(store).apply(
            job.job_id,
            "t1",
            "https://youtu.be/NF-kLy44Hls",
        )
