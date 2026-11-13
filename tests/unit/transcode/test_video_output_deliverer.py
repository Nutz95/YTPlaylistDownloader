from pathlib import Path

from ytpd.domain.job_media_mode import JobMediaMode
from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.job_status import JobStatus
from ytpd.domain.source_kind import SourceKind
from ytpd.domain.track_phase import TrackPhase
from ytpd.domain.track_ref import TrackRef
from ytpd.domain.transcode_backend_kind import TranscodeBackendKind
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths
from ytpd.transcode.video_output_deliverer import VideoOutputDeliverer


def test_deliver_copies_full_video_bytes(tmp_path: Path) -> None:
    paths = TrackArtifactPaths(tmp_path / "work", tmp_path / "out")
    track = TrackRef(
        track_id="vid",
        title="Clip",
        artist="Channel",
        duration_sec=12,
        source_kind=SourceKind.YOUTUBE_VIDEO,
        phase=TrackPhase.DOWNLOADED,
        youtube_url="https://youtu.be/vid",
        deezer_id=None,
        error_message=None,
    )
    job = JobSnapshot(
        job_id="job-1",
        source_url="https://youtu.be/vid",
        source_kind=SourceKind.YOUTUBE_VIDEO,
        status=JobStatus.RUNNING,
        tracks=[track],
        error_message=None,
        media_mode=JobMediaMode.VIDEO,
    )
    source = paths.download_media_file(job, track)
    source.parent.mkdir(parents=True)
    payload = b"fake-mp4-bytes"
    source.write_bytes(payload)

    result = VideoOutputDeliverer(paths).deliver(job, track, TranscodeBackendKind.CPU)

    assert result.success is True
    destination = paths.destination_file(job, track)
    assert destination.read_bytes() == payload
    assert destination.suffix == ".mp4"
