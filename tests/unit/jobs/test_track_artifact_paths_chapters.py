from pathlib import Path

from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.job_status import JobStatus
from ytpd.domain.source_kind import SourceKind
from ytpd.domain.track_phase import TrackPhase
from ytpd.domain.track_ref import TrackRef
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths


def _chapter_track() -> TrackRef:
    return TrackRef(
        track_id="vid__ch00",
        title="Metamorphosis umbrae",
        artist="KageYume",
        duration_sec=138,
        source_kind=SourceKind.YOUTUBE_VIDEO,
        phase=TrackPhase.MATCHED,
        youtube_url="https://youtu.be/vid",
        deezer_id=None,
        error_message=None,
        chapter_start_sec=0.0,
        chapter_end_sec=138.0,
        parent_video_id="vid",
        chapter_index=0,
    )


def test_chapter_tracks_share_parent_download_stem(tmp_path: Path) -> None:
    paths = TrackArtifactPaths(tmp_path / "work", tmp_path / "out")
    job = JobSnapshot(
        job_id="job-1",
        source_url="https://youtu.be/vid",
        source_kind=SourceKind.YOUTUBE_VIDEO,
        status=JobStatus.RUNNING,
        tracks=[_chapter_track()],
        error_message=None,
    )
    track = _chapter_track()
    assert paths.download_media_file(job, track).name == "vid.media"
    assert paths.download_complete_marker(job, track).name == "vid.download"
    assert paths.destination_mp3(track).name == (
        "01 - KageYume - Metamorphosis umbrae.mp3"
    )


def test_plain_track_uses_artist_title_mp3_name(tmp_path: Path) -> None:
    paths = TrackArtifactPaths(tmp_path / "work", tmp_path / "out")
    job = JobSnapshot(
        job_id="job-1",
        source_url="https://youtu.be/plain",
        source_kind=SourceKind.YOUTUBE_VIDEO,
        status=JobStatus.RUNNING,
        tracks=[],
        error_message=None,
    )
    track = TrackRef(
        track_id="deezer-123",
        title="Radioactive",
        artist="Imagine Dragons",
        duration_sec=10,
        source_kind=SourceKind.YOUTUBE_VIDEO,
        phase=TrackPhase.MATCHED,
        youtube_url="https://youtu.be/plain",
        deezer_id="123",
        error_message=None,
    )
    assert paths.download_media_file(job, track).name == "deezer-123.media"
    assert paths.destination_mp3(track).name == "Imagine Dragons - Radioactive.mp3"
