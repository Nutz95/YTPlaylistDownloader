import time
from pathlib import Path

from ytpd.catalog.memory_output_catalog import MemoryOutputCatalog
from ytpd.domain.job_status import JobStatus
from ytpd.domain.source_kind import SourceKind
from ytpd.domain.track_phase import TrackPhase
from ytpd.domain.transcode_backend_kind import TranscodeBackendKind
from ytpd.domain.ytdlp_flat_entry import YtdlpFlatEntry
from ytpd.jobs.job_cancel_flag import JobCancelFlag
from ytpd.jobs.job_download_stack import JobDownloadStack
from ytpd.jobs.job_match_stack import JobMatchStack
from ytpd.jobs.job_orchestrator_stack import JobOrchestratorStack
from ytpd.jobs.job_resolve_stack import JobResolveStack
from ytpd.jobs.job_store import JobStore
from ytpd.jobs.job_transcode_stack import JobTranscodeStack
from ytpd.jobs.sqlite_job_checkpoint_store import SqliteJobCheckpointStore
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths
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
from ytpd.lmstudio.http_lm_studio_client import HttpLmStudioClient
from ytpd.lmstudio.lm_studio_settings import LmStudioSettings


def test_pipeline_runner_starts_immediately_and_completes(tmp_path: Path) -> None:
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
    aborter = NullRequestAborter()
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
        max_workers=1,
        cancel_flag=cancel_flag,
        request_aborter=aborter,
        paths=paths,
        model_runtime=lm_runtime,
    )
    download_stack = JobDownloadStack(
        store,
        work,
        dest,
        FakeMediaDownloader(paths, {"v1"}),
        max_workers=1,
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
    stack = JobOrchestratorStack(
        store,
        work,
        dest,
        resolve_stack.resolve_service,
        match_stack,
        download_stack,
        transcode_stack,
        catalog,
        cancel_flag,
    )
    job = store.create("https://www.youtube.com/playlist?list=demo")
    started = stack.pipeline_runner.start(job.job_id)
    assert started.status is JobStatus.RUNNING
    deadline = time.time() + 10.0
    while time.time() < deadline and stack.pipeline_runner.is_busy():
        time.sleep(0.05)
    assert stack.pipeline_runner.is_busy() is False
    finished = store.get(job.job_id)
    assert finished is not None
    assert finished.status is JobStatus.COMPLETED
    assert finished.pipeline_stage is None
    assert finished.tracks[0].phase is TrackPhase.DONE
    assert finished.tracks[0].source_kind is SourceKind.YOUTUBE_PLAYLIST
