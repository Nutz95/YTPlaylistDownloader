from pathlib import Path

from ytpd.jobs.job_store import JobStore
from ytpd.jobs.job_transcode_stack import JobTranscodeStack
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths
from ytpd.ports.resource_gate import ResourceGate
from ytpd.ports.transcode_progress_store import TranscodeProgressStore
from ytpd.transcode.backend_detect import BackendDetect
from ytpd.transcode.cpu_parallelism import CpuParallelism
from ytpd.transcode.ffmpeg_path_resolver import FfmpegPathResolver


class TranscodeStackFactory:
    """Build a CPU-parallel MP3 transcode stack for the composition root."""

    def build(
        self,
        job_store: JobStore,
        work_dir: Path,
        dest_dir: Path,
        resource_gate: ResourceGate,
        ffmpeg_path: str = "",
        progress_store: TranscodeProgressStore | None = None,
    ) -> JobTranscodeStack:
        """Detect CPU backends and wire the job transcode service."""
        paths = TrackArtifactPaths(work_dir, dest_dir)
        resolved = FfmpegPathResolver(ffmpeg_path).resolve()
        backends = BackendDetect(
            paths,
            CpuParallelism(),
            resolved,
            progress_store,
        ).detect()
        return JobTranscodeStack(
            job_store,
            work_dir,
            dest_dir,
            backends,
            resource_gate,
        )
