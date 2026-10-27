from pathlib import Path

from ytpd.catalog.memory_output_catalog import MemoryOutputCatalog
from ytpd.domain.source_kind import SourceKind
from ytpd.domain.track_phase import TrackPhase
from ytpd.domain.transcode_backend_kind import TranscodeBackendKind
from ytpd.domain.ytdlp_flat_entry import YtdlpFlatEntry
from ytpd.jobs.job_cancel_flag import JobCancelFlag
from ytpd.jobs.job_download_stack import JobDownloadStack
from ytpd.jobs.job_match_stack import JobMatchStack
from ytpd.jobs.job_download_transcode_coordinator import (
    JobDownloadTranscodeCoordinator,
)
from ytpd.jobs.job_orchestrator import JobOrchestrator
from ytpd.jobs.job_resolve_stack import JobResolveStack
from ytpd.jobs.job_store import JobStore
from ytpd.jobs.job_transcode_stack import JobTranscodeStack
from ytpd.jobs.path_track_artifact_probe import PathTrackArtifactProbe
from ytpd.jobs.sqlite_job_checkpoint_store import SqliteJobCheckpointStore
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths
from ytpd.jobs.track_state_machine import TrackStateMachine
from ytpd.match.cascading_youtube_matcher import CascadingYoutubeMatcher
from ytpd.match.static_match_decider import StaticMatchDecider
from ytpd.match.static_match_scorer import StaticMatchScorer
from ytpd.match.youtube_candidate_fetcher import YoutubeCandidateFetcher
from ytpd.runtime.gpu_resource_gate import GpuResourceGate
from ytpd.runtime.null_request_aborter import NullRequestAborter
from tests.fakes.fake_deezer_api_client import FakeDeezerApiClient
from tests.fakes.fake_lm_studio_http_transport import FakeLmStudioHttpTransport
from tests.fakes.fake_lm_studio_model_runtime import FakeLmStudioModelRuntime
from tests.fakes.fake_media_downloader import FakeMediaDownloader
from tests.fakes.fake_transcode_backend import FakeTranscodeBackend
from tests.fakes.fake_youtube_search_client import FakeYoutubeSearchClient
from tests.fakes.fake_ytdlp_flat_playlist_client import FakeYtdlpFlatPlaylistClient
from tests.fakes.fake_ytdlp_video_metadata_client import FakeYtdlpVideoMetadataClient
from tests.fakes.recording_download_transcode_coordinator import (
    RecordingDownloadTranscodeCoordinator,
)
from ytpd.lmstudio.http_lm_studio_client import HttpLmStudioClient
from ytpd.lmstudio.lm_studio_settings import LmStudioSettings


def test_orchestrator_runs_three_track_pipeline_offline(tmp_path: Path) -> None:
    store = JobStore(SqliteJobCheckpointStore(tmp_path / "jobs.db"))
    work = tmp_path / "work"
    dest = tmp_path / "out"
    paths = TrackArtifactPaths(work, dest)
    entries = {
        "https://www.youtube.com/playlist?list=demo": [
            YtdlpFlatEntry(
                video_id="v1",
                title="One",
                uploader="Artist",
                duration_sec=10,
                webpage_url="https://youtu.be/v1",
            ),
            YtdlpFlatEntry(
                video_id="v2",
                title="Two",
                uploader="Artist",
                duration_sec=11,
                webpage_url="https://youtu.be/v2",
            ),
            YtdlpFlatEntry(
                video_id="v3",
                title="Three",
                uploader="Artist",
                duration_sec=12,
                webpage_url="https://youtu.be/v3",
            ),
        ]
    }
    resolve_stack = JobResolveStack(
        store,
        FakeYtdlpFlatPlaylistClient(entries),
        FakeDeezerApiClient({}),
        FakeYtdlpVideoMetadataClient({}),
    )
    gate = GpuResourceGate()
    settings = LmStudioSettings(
        base_url="http://127.0.0.1:1234/v1",
        model="test-model",
        timeout_sec=1.0,
        context_length=8192,
    )
    cancel_flag = JobCancelFlag()
    lm_runtime = FakeLmStudioModelRuntime()
    match_stack = JobMatchStack(
        store,
        CascadingYoutubeMatcher(
            YoutubeCandidateFetcher(FakeYoutubeSearchClient({}), StaticMatchScorer()),
            StaticMatchDecider(),
            HttpLmStudioClient(
                FakeLmStudioHttpTransport(["test-model"], [], offline=True),
                settings,
                lm_runtime,
            ),
            gate,
        ),
        max_workers=2,
        cancel_flag=cancel_flag,
        request_aborter=NullRequestAborter(),
        paths=paths,
        model_runtime=lm_runtime,
    )
    download_stack = JobDownloadStack(
        store,
        work,
        dest,
        FakeMediaDownloader(paths, {"v1", "v2", "v3"}),
        max_workers=2,
        cancel_flag=cancel_flag,
    )
    catalog = MemoryOutputCatalog()
    transcode_stack = JobTranscodeStack(
        store,
        work,
        dest,
        [FakeTranscodeBackend(TranscodeBackendKind.CPU, paths)],
        gate,
        catalog=catalog,
    )
    coordinator = JobDownloadTranscodeCoordinator(
        store,
        download_stack.download_pool,
        transcode_stack.scheduler,
        PathTrackArtifactProbe(paths),
        TrackStateMachine(),
        paths,
        cancel_flag,
        download_stack.failure_log,
        download_stack.phase_healer,
    )
    orchestrator = JobOrchestrator(
        store,
        resolve_stack.resolve_service,
        match_stack.match_service,
        coordinator,
        PathTrackArtifactProbe(paths),
        catalog,
        cancel_flag,
        lm_runtime,
    )
    job = store.create("https://www.youtube.com/playlist?list=demo")
    result = orchestrator.run_job(job.job_id)
    assert result.cancelled is False
    assert len(result.snapshot.tracks) == 3
    assert all(track.phase is TrackPhase.DONE for track in result.snapshot.tracks)
    assert all(track.source_kind is SourceKind.YOUTUBE_PLAYLIST for track in result.snapshot.tracks)
    assert len(catalog.list_entries()) == 3
    assert lm_runtime.release_calls == 1


def test_orchestrator_releases_lm_before_media_pipeline(tmp_path: Path) -> None:
    store = JobStore(SqliteJobCheckpointStore(tmp_path / "jobs.db"))
    work = tmp_path / "work"
    dest = tmp_path / "out"
    paths = TrackArtifactPaths(work, dest)
    events: list[str] = []
    lm_runtime = FakeLmStudioModelRuntime(events)
    cancel_flag = JobCancelFlag()
    resolve_stack = JobResolveStack(
        store,
        FakeYtdlpFlatPlaylistClient(
            {
                "https://www.youtube.com/playlist?list=demo": [
                    YtdlpFlatEntry(
                        video_id="v1",
                        title="One",
                        uploader="Artist",
                        duration_sec=10,
                        webpage_url="https://youtu.be/v1",
                    )
                ]
            }
        ),
        FakeDeezerApiClient({}),
        FakeYtdlpVideoMetadataClient({}),
    )
    settings = LmStudioSettings(
        base_url="http://127.0.0.1:1234/v1",
        model="test-model",
        timeout_sec=1.0,
        context_length=8192,
    )
    match_stack = JobMatchStack(
        store,
        CascadingYoutubeMatcher(
            YoutubeCandidateFetcher(FakeYoutubeSearchClient({}), StaticMatchScorer()),
            StaticMatchDecider(),
            HttpLmStudioClient(
                FakeLmStudioHttpTransport(["test-model"], [], offline=True),
                settings,
                lm_runtime,
            ),
            GpuResourceGate(),
        ),
        max_workers=1,
        cancel_flag=cancel_flag,
        request_aborter=NullRequestAborter(),
        paths=paths,
        model_runtime=lm_runtime,
    )
    orchestrator = JobOrchestrator(
        store,
        resolve_stack.resolve_service,
        match_stack.match_service,
        RecordingDownloadTranscodeCoordinator(store, events),
        PathTrackArtifactProbe(paths),
        MemoryOutputCatalog(),
        cancel_flag,
        lm_runtime,
    )
    job = store.create("https://www.youtube.com/playlist?list=demo")
    orchestrator.run_job(job.job_id)
    assert "release" in events
    assert "media" in events
    assert events.index("release") < events.index("media")
