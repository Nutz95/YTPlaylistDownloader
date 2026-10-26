import subprocess
import sys
from pathlib import Path

from ytpd.domain.download_attempt_mode import DownloadAttemptMode
from ytpd.domain.download_result import DownloadResult
from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.track_ref import TrackRef
from ytpd.domain.ytdlp_download_attempt import YtdlpDownloadAttempt
from ytpd.download.download_resume_policy import DownloadResumePolicy
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths

_DOWNLOAD_TIMEOUT_SEC = 600.0


class YtdlpDownloader:
    """Download track media with yt-dlp, applying resume-or-full policy."""

    def __init__(
        self,
        paths: TrackArtifactPaths,
        policy: DownloadResumePolicy,
        max_attempts: int = 2,
    ) -> None:
        self._paths = paths
        self._policy = policy
        self._max_attempts = max(1, max_attempts)

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
        if self._is_complete(media, marker):
            return DownloadResult(
                track_id=track.track_id,
                success=True,
                output_path=str(media),
                error_message=None,
                bytes_downloaded=media.stat().st_size,
            )
        if marker.is_file():
            marker.unlink()
        self._paths.job_work_dir(job).mkdir(parents=True, exist_ok=True)
        partial = self._paths.download_partial_file(job, track)
        last_error = "download failed"
        for _ in range(self._max_attempts):
            mode = self._policy.decide(partial)
            attempt = self._run_ytdlp(track.youtube_url, media, mode)
            if attempt.success and media.is_file() and media.stat().st_size > 0:
                return DownloadResult(
                    track_id=track.track_id,
                    success=True,
                    output_path=str(media),
                    error_message=None,
                    bytes_downloaded=media.stat().st_size,
                )
            last_error = attempt.detail
            self._policy.clear_partial(partial)
        return DownloadResult(
            track_id=track.track_id,
            success=False,
            output_path=None,
            error_message=last_error,
            bytes_downloaded=0,
        )

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
    ) -> YtdlpDownloadAttempt:
        argv = [
            sys.executable,
            "-m",
            "yt_dlp",
            "--no-playlist",
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
            completed = subprocess.run(
                argv,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=_DOWNLOAD_TIMEOUT_SEC,
            )
        except OSError as error:
            return YtdlpDownloadAttempt(
                success=False,
                detail=f"yt-dlp unavailable: {error}",
            )
        except subprocess.TimeoutExpired:
            return YtdlpDownloadAttempt(
                success=False,
                detail="yt-dlp download timed out",
            )
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip() or "unknown"
            return YtdlpDownloadAttempt(
                success=False,
                detail=f"yt-dlp download failed: {detail}",
            )
        return YtdlpDownloadAttempt(success=True, detail="ok")
