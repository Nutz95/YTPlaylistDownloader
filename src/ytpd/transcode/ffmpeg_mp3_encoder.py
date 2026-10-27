import subprocess
import time
from pathlib import Path

from ytpd.domain.ffmpeg_encode_request import FfmpegEncodeRequest
from ytpd.domain.transcode_backend_kind import TranscodeBackendKind
from ytpd.domain.transcode_progress_snapshot import TranscodeProgressSnapshot
from ytpd.domain.transcode_result import TranscodeResult
from ytpd.ports.transcode_progress_store import TranscodeProgressStore
from ytpd.runtime.subprocess_text_runner import SubprocessTextRunner
from ytpd.transcode.ffmpeg_progress_parser import FfmpegProgressParser

_BITRATE = "192k"
_TIMEOUT_SEC = 600.0
_BACKEND_LABELS = {
    TranscodeBackendKind.CPU: "CPU",
    TranscodeBackendKind.NVIDIA: "NVIDIA",
    TranscodeBackendKind.ARC: "ARC",
}


class FfmpegMp3Encoder:
    """Run ffmpeg to produce an atomic MP3 from a downloaded media file."""

    def __init__(
        self,
        runner: SubprocessTextRunner,
        ffmpeg_path: str,
        progress_store: TranscodeProgressStore | None = None,
    ) -> None:
        cleaned = ffmpeg_path.strip()
        if cleaned == "":
            raise ValueError("ffmpeg_path must be a non-empty string")
        self._runner = runner
        self._ffmpeg_path = cleaned
        self._progress_store = progress_store
        self._progress_parser = FfmpegProgressParser()

    def encode(self, request: FfmpegEncodeRequest) -> TranscodeResult:
        """Encode ``request.source`` to ``request.destination`` at 192 kbps CBR."""
        source = request.source
        destination = request.destination
        if not source.is_file() or source.stat().st_size <= 0:
            return self._failure(request.track_id, request.backend, "missing download media")
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = self._temporary_path(destination, request.track_id)
        self._unlink_quiet(temporary)
        self._publish(request, "starting", None, "starting ffmpeg")
        attempt = self._run_ffmpeg(request, temporary)
        if attempt != "ok" or not temporary.is_file():
            self._unlink_quiet(temporary)
            self._publish(request, "failed", None, attempt)
            self._clear_progress(request.track_id)
            return self._failure(request.track_id, request.backend, attempt)
        temporary.replace(destination)
        self._publish(request, "complete", 100.0, "encode complete")
        self._clear_progress(request.track_id)
        return TranscodeResult(
            track_id=request.track_id,
            success=True,
            output_path=str(destination),
            backend=request.backend,
            error_message=None,
        )

    def _run_ffmpeg(self, request: FfmpegEncodeRequest, temporary: Path) -> str:
        if self._progress_store is None:
            return self._run_ffmpeg_blocking(request, temporary)
        return self._run_ffmpeg_with_progress(request, temporary)

    def _run_ffmpeg_blocking(self, request: FfmpegEncodeRequest, temporary: Path) -> str:
        argv = self._build_argv(request, temporary, with_progress=False)
        try:
            completed = self._runner.run(argv, _TIMEOUT_SEC)
        except OSError as error:
            return f"ffmpeg unavailable: {error}"
        except subprocess.TimeoutExpired:
            return "ffmpeg timed out"
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip() or "unknown"
            return f"ffmpeg failed: {detail}"
        return "ok"

    def _run_ffmpeg_with_progress(
        self,
        request: FfmpegEncodeRequest,
        temporary: Path,
    ) -> str:
        argv = self._build_argv(request, temporary, with_progress=True)
        try:
            process = subprocess.Popen(
                argv,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except OSError as error:
            return f"ffmpeg unavailable: {error}"
        return self._consume_progress(process, request)

    def _consume_progress(
        self,
        process: subprocess.Popen[str],
        request: FfmpegEncodeRequest,
    ) -> str:
        deadline = time.monotonic() + _TIMEOUT_SEC
        stream = process.stdout
        stderr_chunks: list[str] = []
        if stream is None:
            process.kill()
            return "ffmpeg stdout missing"
        while True:
            if time.monotonic() > deadline:
                process.kill()
                process.wait(timeout=5)
                return "ffmpeg timed out"
            line = stream.readline()
            if line == "" and process.poll() is not None:
                break
            if line == "":
                time.sleep(0.02)
                continue
            self._handle_progress_line(request, line)
        err = process.stderr
        if err is not None:
            stderr_chunks.append(err.read())
        return_code = process.wait(timeout=5)
        if return_code != 0:
            detail = "".join(stderr_chunks).strip() or "unknown"
            return f"ffmpeg failed: {detail}"
        return "ok"

    def _handle_progress_line(self, request: FfmpegEncodeRequest, line: str) -> None:
        if self._progress_parser.is_end(line):
            self._publish(request, "encoding", 100.0, "finishing")
            return
        elapsed = self._progress_parser.elapsed_sec(line)
        if elapsed is None:
            return
        duration = request.expected_duration_sec
        percent: float | None = None
        if duration is not None and duration > 0:
            percent = min(99.0, (elapsed / duration) * 100.0)
        self._publish(request, "encoding", percent, f"t={elapsed:.1f}s")

    def _build_argv(
        self,
        request: FfmpegEncodeRequest,
        temporary: Path,
        with_progress: bool,
    ) -> list[str]:
        argv = [self._ffmpeg_path, "-y", "-threads", "0"]
        if with_progress:
            argv.extend(["-nostats", "-progress", "pipe:1"])
        argv.extend(["-i", str(request.source)])
        if (
            request.chapter_start_sec is not None
            and request.chapter_duration_sec is not None
        ):
            argv.extend(
                [
                    "-ss",
                    f"{request.chapter_start_sec:.3f}",
                    "-t",
                    f"{request.chapter_duration_sec:.3f}",
                ]
            )
        argv.extend(["-vn", "-codec:a", "libmp3lame", "-b:a", _BITRATE])
        if request.metadata_title is not None and request.metadata_title.strip() != "":
            argv.extend(["-metadata", f"title={request.metadata_title}"])
        if request.metadata_artist is not None and request.metadata_artist.strip() != "":
            argv.extend(["-metadata", f"artist={request.metadata_artist}"])
        # Temp path ends with ``.mp3.tmp`` — ffmpeg cannot infer mp3 from that.
        argv.extend(["-f", "mp3", str(temporary)])
        return argv

    def _publish(
        self,
        request: FfmpegEncodeRequest,
        status: str,
        percent: float | None,
        message: str,
    ) -> None:
        if self._progress_store is None:
            return
        self._progress_store.set_snapshot(
            TranscodeProgressSnapshot(
                track_id=request.track_id,
                status=status,
                backend_label=_BACKEND_LABELS.get(request.backend, "CPU"),
                percent=percent,
                message=message,
            )
        )

    def _clear_progress(self, track_id: str) -> None:
        if self._progress_store is None:
            return
        self._progress_store.clear(track_id)

    def _temporary_path(self, destination: Path, track_id: str) -> Path:
        safe_id = "".join(
            char if char.isalnum() or char in "-_" else "_" for char in track_id
        )
        return destination.parent / f".{safe_id}.mp3.tmp"

    def _unlink_quiet(self, path: Path) -> None:
        if not path.is_file():
            return
        try:
            path.unlink()
        except OSError:
            return

    def _failure(
        self,
        track_id: str,
        backend: TranscodeBackendKind,
        message: str,
    ) -> TranscodeResult:
        return TranscodeResult(
            track_id=track_id,
            success=False,
            output_path=None,
            backend=backend,
            error_message=message,
        )
