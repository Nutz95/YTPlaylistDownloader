import subprocess
from pathlib import Path

from ytpd.domain.transcode_backend_kind import TranscodeBackendKind
from ytpd.domain.transcode_result import TranscodeResult

_BITRATE = "192k"
_TIMEOUT_SEC = 600.0


class FfmpegMp3Encoder:
    """Run ffmpeg to produce an atomic MP3 from a downloaded media file."""

    def encode(
        self,
        track_id: str,
        source: Path,
        destination: Path,
        backend: TranscodeBackendKind,
    ) -> TranscodeResult:
        """Encode ``source`` to ``destination`` at 192 kbps CBR."""
        if not source.is_file() or source.stat().st_size <= 0:
            return self._failure(track_id, backend, "missing download media")
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(".mp3.tmp")
        if temporary.is_file():
            temporary.unlink()
        attempt = self._run_ffmpeg(source, temporary)
        if attempt != "ok" or not temporary.is_file():
            if temporary.is_file():
                temporary.unlink()
            return self._failure(track_id, backend, attempt)
        temporary.replace(destination)
        return TranscodeResult(
            track_id=track_id,
            success=True,
            output_path=str(destination),
            backend=backend,
            error_message=None,
        )

    def _run_ffmpeg(self, source: Path, temporary: Path) -> str:
        argv = [
            "ffmpeg",
            "-y",
            "-i",
            str(source),
            "-vn",
            "-codec:a",
            "libmp3lame",
            "-b:a",
            _BITRATE,
            str(temporary),
        ]
        try:
            completed = subprocess.run(
                argv,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=_TIMEOUT_SEC,
            )
        except OSError as error:
            return f"ffmpeg unavailable: {error}"
        except subprocess.TimeoutExpired:
            return "ffmpeg timed out"
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip() or "unknown"
            return f"ffmpeg failed: {detail}"
        return "ok"

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
