import threading
from concurrent.futures import ThreadPoolExecutor

from ytpd.domain.catalog_entry import CatalogEntry
from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.track_ref import TrackRef
from ytpd.domain.transcode_backend_kind import TranscodeBackendKind
from ytpd.domain.transcode_result import TranscodeResult
from ytpd.ports.output_catalog import OutputCatalog
from ytpd.ports.resource_gate import ResourceGate
from ytpd.ports.transcode_backend import TranscodeBackend

_GPU_KINDS = {TranscodeBackendKind.NVIDIA, TranscodeBackendKind.ARC}


class TranscodeScheduler:
    """Schedule track transcodes with GPU-first priority and LLM exclusion."""

    def __init__(
        self,
        backends: list[TranscodeBackend],
        resource_gate: ResourceGate,
        catalog: OutputCatalog,
    ) -> None:
        self._backends = list(backends)
        self._resource_gate = resource_gate
        self._catalog = catalog
        self._condition = threading.Condition()
        self._busy = {id(backend): False for backend in self._backends}

    def backend_count(self) -> int:
        """Return how many parallel encode slots this scheduler owns."""
        return max(1, len(self._backends))

    def run(self, job: JobSnapshot, tracks: list[TrackRef]) -> list[TranscodeResult]:
        """Transcode ``tracks`` in parallel and upsert catalogue entries."""
        if len(tracks) == 0 or len(self._backends) == 0:
            return []
        with ThreadPoolExecutor(max_workers=len(self._backends)) as pool:
            return list(
                pool.map(lambda track: self.transcode_track(job, track), tracks)
            )

    def transcode_track(
        self,
        job: JobSnapshot,
        track: TrackRef,
    ) -> TranscodeResult:
        """Transcode one track (claims a backend) and upsert the catalogue on success."""
        if len(self._backends) == 0:
            return TranscodeResult(
                track_id=track.track_id,
                success=False,
                output_path=None,
                backend=None,
                error_message="no transcode backend available",
            )
        backend = self._claim_backend()
        try:
            result = backend.transcode(job, track)
        finally:
            self._release_backend(backend)
        if result.success and result.output_path is not None:
            self._catalog.upsert(
                CatalogEntry(
                    track_id=track.track_id,
                    title=track.title,
                    artist=track.artist,
                    mp3_path=result.output_path,
                    youtube_url=track.youtube_url,
                    deezer_id=track.deezer_id,
                )
            )
        return result

    def _claim_backend(self) -> TranscodeBackend:
        with self._condition:
            while True:
                for backend in self._backends:
                    if self._busy[id(backend)]:
                        continue
                    if backend.kind() in _GPU_KINDS:
                        if not self._resource_gate.try_acquire_gpu():
                            continue
                    self._busy[id(backend)] = True
                    return backend
                self._condition.wait(timeout=0.05)

    def _release_backend(self, backend: TranscodeBackend) -> None:
        with self._condition:
            self._busy[id(backend)] = False
            if backend.kind() in _GPU_KINDS:
                self._resource_gate.release_gpu()
            self._condition.notify_all()
