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
from tests.fakes.pipeline_runner_test_stack import PipelineRunnerTestStack
from ytpd.lmstudio.http_lm_studio_client import HttpLmStudioClient
from ytpd.lmstudio.lm_studio_settings import LmStudioSettings


def _build_stack(
    tmp_path: Path,
    playlist_entries: dict[str, list[YtdlpFlatEntry]],
    download_ids: set[str],
) -> PipelineRunnerTestStack:
    store = JobStore(SqliteJobCheckpointStore(tmp_path / "jobs.db"))
    work = tmp_path / "work"
    dest = tmp_path / "out"
    paths = TrackArtifactPaths(work, dest)
    resolve_stack = JobResolveStack(
        store,
        FakeYtdlpFlatPlaylistClient(playlist_entries),
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
        FakeMediaDownloader(paths, download_ids),
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
    return PipelineRunnerTestStack(store=store, stack=stack)


def _wait_idle(stack: JobOrchestratorStack, timeout_sec: float = 10.0) -> None:
    deadline = time.time() + timeout_sec
    while time.time() < deadline and stack.pipeline_runner.is_busy():
        time.sleep(0.05)
    assert stack.pipeline_runner.is_busy() is False


def test_pipeline_runner_starts_immediately_and_completes(tmp_path: Path) -> None:
    url = "https://www.youtube.com/playlist?list=demo"
    entries = {
        url: [
            YtdlpFlatEntry(
                video_id="v1",
                title="One",
                uploader="Artist",
                duration_sec=10,
                webpage_url="https://youtu.be/v1",
            ),
        ]
    }
    harness = _build_stack(tmp_path, entries, {"v1"})
    job = harness.store.create(url)
    started = harness.stack.pipeline_runner.start(job.job_id)
    assert started.status is JobStatus.RUNNING
    _wait_idle(harness.stack)
    finished = harness.store.get(job.job_id)
    assert finished is not None
    assert finished.status is JobStatus.COMPLETED
    assert finished.pipeline_stage is None
    assert finished.tracks[0].phase is TrackPhase.DONE
    assert finished.tracks[0].source_kind is SourceKind.YOUTUBE_PLAYLIST


def test_pipeline_runner_drains_queued_job_when_first_completes(tmp_path: Path) -> None:
    url_a = "https://www.youtube.com/playlist?list=a"
    url_b = "https://www.youtube.com/playlist?list=b"
    entries = {
        url_a: [
            YtdlpFlatEntry(
                video_id="va",
                title="A",
                uploader="Artist",
                duration_sec=10,
                webpage_url="https://youtu.be/va",
            ),
        ],
        url_b: [
            YtdlpFlatEntry(
                video_id="vb",
                title="B",
                uploader="Artist",
                duration_sec=10,
                webpage_url="https://youtu.be/vb",
            ),
        ],
    }
    harness = _build_stack(tmp_path, entries, {"va", "vb"})
    first = harness.store.create(url_a)
    second = harness.store.create(url_b)
    harness.stack.pipeline_runner.start(first.job_id)
    _wait_idle(harness.stack)
    finished_first = harness.store.get(first.job_id)
    finished_second = harness.store.get(second.job_id)
    assert finished_first is not None
    assert finished_second is not None
    assert finished_first.status is JobStatus.COMPLETED
    assert finished_second.status is JobStatus.COMPLETED
    assert finished_second.tracks[0].phase is TrackPhase.DONE


def test_drain_queue_starts_interrupted_job_when_idle(tmp_path: Path) -> None:
    url = "https://www.youtube.com/playlist?list=resume"
    entries = {
        url: [
            YtdlpFlatEntry(
                video_id="vr",
                title="R",
                uploader="Artist",
                duration_sec=10,
                webpage_url="https://youtu.be/vr",
            ),
        ]
    }
    harness = _build_stack(tmp_path, entries, {"vr"})
    job = harness.store.create(url)
    harness.store.save(job.with_status(JobStatus.INTERRUPTED))
    started = harness.stack.pipeline_runner.drain_queue()
    assert started is not None
    assert started.job_id == job.job_id
    assert started.status is JobStatus.RUNNING
    _wait_idle(harness.stack)
    finished = harness.store.get(job.job_id)
    assert finished is not None
    assert finished.status is JobStatus.COMPLETED
