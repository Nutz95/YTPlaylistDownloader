from pathlib import Path

from ytpd.jobs.job_store import JobStore
from ytpd.jobs.job_transcode_stack import JobTranscodeStack
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths
from ytpd.ports.resource_gate import ResourceGate
from ytpd.transcode.backend_detect import BackendDetect
from ytpd.transcode.cpu_parallelism import CpuParallelism


class TranscodeStackFactory:
    """Build a GPU-first transcode stack for the composition root."""

    def build(
        self,
        job_store: JobStore,
        work_dir: Path,
        dest_dir: Path,
        resource_gate: ResourceGate,
    ) -> JobTranscodeStack:
        """Detect backends and wire the job transcode service."""
        paths = TrackArtifactPaths(work_dir, dest_dir)
        backends = BackendDetect(paths, CpuParallelism()).detect()
        return JobTranscodeStack(
            job_store,
            work_dir,
            dest_dir,
            backends,
            resource_gate,
        )
