import subprocess
import threading
import time
from pathlib import Path

from ytpd.domain.download_attempt_mode import DownloadAttemptMode
from ytpd.domain.download_progress_snapshot import DownloadProgressSnapshot
from ytpd.domain.download_result import DownloadResult
from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.track_ref import TrackRef
from ytpd.domain.ytdlp_download_attempt import YtdlpDownloadAttempt
from ytpd.download.download_resume_policy import DownloadResumePolicy
from ytpd.download.ytdlp_download_error_hint import YtdlpDownloadErrorHint
from ytpd.download.ytdlp_progress_line_parser import YtdlpProgressLineParser
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths
from ytpd.ports.download_progress_store import DownloadProgressStore
from ytpd.resolve.ytdlp_argv_builder import YtdlpArgvBuilder

_DOWNLOAD_TIMEOUT_SEC = 3600.0


class YtdlpDownloader:
    """Download track media with yt-dlp, applying resume-or-full policy."""

    def __init__(
        self,
        paths: TrackArtifactPaths,
        policy: DownloadResumePolicy,
        progress_store: DownloadProgressStore,
        argv_builder: YtdlpArgvBuilder,
        max_attempts: int = 2,
    ) -> None:
        self._paths = paths
        self._policy = policy
        self._progress_store = progress_store
        self._progress_parser = YtdlpProgressLineParser()
        self._max_attempts = max(1, max_attempts)
        self._argv_builder = argv_builder
        self._error_hint = YtdlpDownloadErrorHint()
        self._media_locks: dict[str, threading.Lock] = {}
        self._media_locks_guard = threading.Lock()

    def download(self, job: JobSnapshot, track: TrackRef) -> DownloadResult:
        """Download ``track`` media, retrying full after a failed resume."""
        if track.youtube_url is None or track.youtube_url.strip() == "":
            return DownloadResult(
                track_id=track.track_id,
                success=False,
                output_path=None,
                error_message="missing youtube url",
                bytes_downloaded=0,
            )
        media = self._paths.download_media_file(job, track)
        marker = self._paths.download_complete_marker(job, track)
        media_key = self._paths.download_media_key(track)
        lock = self._lock_for(media)
        self._publish(
            media_key,
            status="waiting",
            percent=None,
            downloaded_bytes=None,
            total_bytes=None,
            message="waiting for download slot",
        )
        with lock:
            try:
                return self._download_locked(job, track, media, marker, media_key)
            finally:
                self._progress_store.clear(media_key)

    def _download_locked(
        self,
        job: JobSnapshot,
        track: TrackRef,
        media: Path,
        marker: Path,
        media_key: str,
    ) -> DownloadResult:
        if self._is_complete(media, marker):
            return self._success_result(track.track_id, media, media_key, "already downloaded")
        if marker.is_file():
            marker.unlink()
        self._paths.job_work_dir(job).mkdir(parents=True, exist_ok=True)
        youtube_url = track.youtube_url
        if youtube_url is None:
            return DownloadResult(
                track_id=track.track_id,
                success=False,
                output_path=None,
                error_message="missing youtube url",
                bytes_downloaded=0,
            )
        return self._download_attempts(
            track.track_id,
            youtube_url,
            media,
            self._paths.download_partial_file(job, track),
            media_key,
        )

    def _download_attempts(
        self,
        track_id: str,
        youtube_url: str,
        media: Path,
        partial: Path,
        media_key: str,
    ) -> DownloadResult:
        last_error = "download failed"
        for _ in range(self._max_attempts):
            mode = self._policy.decide(partial)
            self._publish(
                media_key,
                status="starting",
                percent=0.0,
                downloaded_bytes=None,
                total_bytes=None,
                message="starting yt-dlp",
            )
            attempt = self._run_ytdlp(youtube_url, media, mode, media_key)
            if attempt.success and media.is_file() and media.stat().st_size > 0:
                return self._success_result(
                    track_id, media, media_key, "download complete"
                )
            last_error = self._error_hint.enrich(attempt.detail)
            self._publish(
                media_key,
                status="failed",
                percent=None,
                downloaded_bytes=None,
                total_bytes=None,
                message=last_error,
            )
            self._policy.clear_partial(partial)
        return DownloadResult(
            track_id=track_id,
            success=False,
            output_path=None,
            error_message=last_error,
            bytes_downloaded=0,
        )

    def _success_result(
        self,
        track_id: str,
        media: Path,
        media_key: str,
        message: str,
    ) -> DownloadResult:
        size = media.stat().st_size
        self._publish(
            media_key,
            status="complete",
            percent=100.0,
            downloaded_bytes=size,
            total_bytes=size,
            message=message,
        )
        return DownloadResult(
            track_id=track_id,
            success=True,
            output_path=str(media),
            error_message=None,
            bytes_downloaded=size,
        )

    def _lock_for(self, media: Path) -> threading.Lock:
        key = str(media)
        with self._media_locks_guard:
            lock = self._media_locks.get(key)
            if lock is None:
                lock = threading.Lock()
                self._media_locks[key] = lock
            return lock

    def _is_complete(self, media: Path, marker: Path) -> bool:
        return (
            marker.is_file()
            and media.is_file()
            and media.stat().st_size > 0
        )

    def _run_ytdlp(
        self,
        url: str,
        media_path: Path,
        mode: DownloadAttemptMode,
        media_key: str,
    ) -> YtdlpDownloadAttempt:
        argv = [
            *self._argv_builder.prefix(),
            "--no-playlist",
            "--newline",
            "-f",
            "bestaudio/best",
            "-o",
            str(media_path),
        ]
        if mode is DownloadAttemptMode.RESUME:
            argv.append("--continue")
        else:
            argv.append("--no-continue")
        argv.append(url)
        try:
            process = subprocess.Popen(
                argv,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except OSError as error:
            return YtdlpDownloadAttempt(
                success=False,
                detail=f"yt-dlp unavailable: {error}",
            )
        return self._consume_process(process, media_key)

    def _consume_process(
        self,
        process: subprocess.Popen[str],
        media_key: str,
    ) -> YtdlpDownloadAttempt:
        output_lines: list[str] = []
        deadline = time.monotonic() + _DOWNLOAD_TIMEOUT_SEC
        stream = process.stdout
        if stream is None:
            process.kill()
            return YtdlpDownloadAttempt(success=False, detail="yt-dlp stdout missing")
        while True:
            if time.monotonic() > deadline:
                process.kill()
                process.wait(timeout=5)
                return YtdlpDownloadAttempt(
                    success=False,
                    detail="yt-dlp download timed out",
                )
            line = stream.readline()
            if line == "" and process.poll() is not None:
                break
            if line == "":
                time.sleep(0.05)
                continue
            output_lines.append(line.rstrip())
            parsed = self._progress_parser.parse(line)
            if parsed is None:
                continue
            self._publish(
                media_key,
                status="downloading",
                percent=parsed.percent,
                downloaded_bytes=parsed.downloaded_bytes,
                total_bytes=parsed.total_bytes,
                message=parsed.message,
            )
        return_code = process.wait(timeout=5)
        if return_code != 0:
            detail = "\n".join(output_lines[-8:]).strip() or "unknown"
            return YtdlpDownloadAttempt(
                success=False,
                detail=f"yt-dlp download failed: {detail}",
            )
        return YtdlpDownloadAttempt(success=True, detail="ok")

    def _publish(
        self,
        media_key: str,
        status: str,
        percent: float | None,
        downloaded_bytes: int | None,
        total_bytes: int | None,
        message: str,
    ) -> None:
        self._progress_store.set_snapshot(
            DownloadProgressSnapshot(
                media_key=media_key,
                status=status,
                percent=percent,
                downloaded_bytes=downloaded_bytes,
                total_bytes=total_bytes,
                message=message,
            )
        )
