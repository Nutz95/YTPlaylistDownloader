from ytpd.domain.download_progress_snapshot import DownloadProgressSnapshot
from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.job_status import JobStatus
from ytpd.domain.pipeline_stage import PipelineStage
from ytpd.domain.source_kind import SourceKind
from ytpd.domain.track_phase import TrackPhase
from ytpd.domain.track_ref import TrackRef
from ytpd.domain.transcode_progress_snapshot import TranscodeProgressSnapshot
from ytpd.download.memory_download_progress_store import MemoryDownloadProgressStore
from ytpd.jobs.progress_calculator import ProgressCalculator
from ytpd.transcode.memory_transcode_progress_store import MemoryTranscodeProgressStore


def test_global_percent_and_active_media_filter() -> None:
    store = MemoryDownloadProgressStore()
    store.set_snapshot(
        DownloadProgressSnapshot(
            media_key="2",
            status="downloading",
            percent=42.5,
            downloaded_bytes=1_048_576,
            total_bytes=2_097_152,
            message="[download] 42.5%",
        )
    )
    job = JobSnapshot(
        job_id="j1",
        source_url="https://example.test/list",
        source_kind=SourceKind.YOUTUBE_PLAYLIST,
        status=JobStatus.RUNNING,
        tracks=[
            TrackRef(
                track_id="1",
                title="Done",
                artist="A",
                duration_sec=10,
                source_kind=SourceKind.YOUTUBE_PLAYLIST,
                phase=TrackPhase.DONE,
                youtube_url="https://youtu.be/1",
                deezer_id=None,
                error_message=None,
            ),
            TrackRef(
                track_id="2",
                title="DL",
                artist="B",
                duration_sec=20,
                source_kind=SourceKind.YOUTUBE_PLAYLIST,
                phase=TrackPhase.DOWNLOADING,
                youtube_url="https://youtu.be/2",
                deezer_id=None,
                error_message=None,
            ),
        ],
        error_message=None,
        pipeline_stage=PipelineStage.DOWNLOAD,
    )
    snapshot = ProgressCalculator(store).from_job(job)
    assert snapshot.job_status is JobStatus.RUNNING
    assert snapshot.global_progress.percent == 77.5
    assert snapshot.global_progress.stage == "download"
    assert snapshot.global_progress.stage_done == 1
    assert snapshot.global_progress.stage_total == 2
    assert "B — DL" in snapshot.global_progress.label
    assert len(snapshot.active_media) == 1
    assert snapshot.active_media[0].track_id == "2"
    assert snapshot.active_media[0].artist == "B"
    assert "42.5%" in snapshot.active_media[0].detail
    assert snapshot.failed_media == []


def test_match_stage_counts_matched_tracks() -> None:
    job = JobSnapshot(
        job_id="j2",
        source_url="https://example.test/list",
        source_kind=SourceKind.DEEZER_PLAYLIST,
        status=JobStatus.RUNNING,
        tracks=[
            TrackRef(
                track_id="1",
                title="One",
                artist="A",
                duration_sec=10,
                source_kind=SourceKind.DEEZER_PLAYLIST,
                phase=TrackPhase.MATCHED,
                youtube_url="https://youtu.be/1",
                deezer_id="d1",
                error_message=None,
            ),
            TrackRef(
                track_id="2",
                title="Two",
                artist="B",
                duration_sec=11,
                source_kind=SourceKind.DEEZER_PLAYLIST,
                phase=TrackPhase.MATCHING,
                youtube_url=None,
                deezer_id="d2",
                error_message=None,
            ),
        ],
        error_message=None,
        pipeline_stage=PipelineStage.MATCH,
    )
    snapshot = ProgressCalculator(MemoryDownloadProgressStore()).from_job(job)
    assert snapshot.global_progress.stage_done == 1
    assert snapshot.global_progress.stage_total == 2
    assert snapshot.active_media[0].phase is TrackPhase.MATCHING
    assert snapshot.active_media[0].detail == "matching…"


def test_transcoding_detail_shows_cpu_percent() -> None:
    transcode_store = MemoryTranscodeProgressStore()
    transcode_store.set_snapshot(
        TranscodeProgressSnapshot(
            track_id="3",
            status="encoding",
            backend_label="CPU",
            percent=55.0,
            message="t=10s",
        )
    )
    job = JobSnapshot(
        job_id="j3",
        source_url="https://example.test/list",
        source_kind=SourceKind.DEEZER_PLAYLIST,
        status=JobStatus.RUNNING,
        tracks=[
            TrackRef(
                track_id="3",
                title="Enc",
                artist="C",
                duration_sec=30,
                source_kind=SourceKind.DEEZER_PLAYLIST,
                phase=TrackPhase.TRANSCODING,
                youtube_url="https://youtu.be/3",
                deezer_id="d3",
                error_message=None,
            ),
        ],
        error_message=None,
        pipeline_stage=PipelineStage.TRANSCODE,
    )
    snapshot = ProgressCalculator(
        MemoryDownloadProgressStore(),
        transcode_store,
        transcode_slot_count=22,
    ).from_job(job)
    assert "CPU×22" in snapshot.global_progress.label
    assert "1 encoding" in snapshot.global_progress.label
    assert snapshot.active_media[0].detail == "CPU · 55%"


def test_transcoding_when_pipeline_stopped_explains_resume() -> None:
    job = JobSnapshot(
        job_id="j4",
        source_url="https://example.test/list",
        source_kind=SourceKind.DEEZER_PLAYLIST,
        status=JobStatus.FAILED,
        tracks=[
            TrackRef(
                track_id="4",
                title="Stuck",
                artist="D",
                duration_sec=30,
                source_kind=SourceKind.DEEZER_PLAYLIST,
                phase=TrackPhase.TRANSCODING,
                youtube_url="https://youtu.be/4",
                deezer_id="d4",
                error_message=None,
            ),
        ],
        error_message="boom",
        pipeline_stage=None,
    )
    snapshot = ProgressCalculator(MemoryDownloadProgressStore()).from_job(job)
    assert "Resume" in snapshot.active_media[0].detail
