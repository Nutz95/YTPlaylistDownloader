from ytpd.domain.download_result import DownloadResult
from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.track_ref import TrackRef
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths


class FakeMediaDownloader:
    """Write media files for configured track ids; fail the others."""

    def __init__(
        self,
        paths: TrackArtifactPaths,
        success_ids: set[str],
    ) -> None:
        self._paths = paths
        self._success_ids = set(success_ids)
        self.calls: list[str] = []

    def download(self, job: JobSnapshot, track: TrackRef) -> DownloadResult:
        """Create a fake media file when the track id is allowed."""
        self.calls.append(track.track_id)
        if track.track_id not in self._success_ids:
            return DownloadResult(
                track_id=track.track_id,
                success=False,
                output_path=None,
                error_message="fake download failed",
                bytes_downloaded=0,
            )
        work = self._paths.job_work_dir(job)
        work.mkdir(parents=True, exist_ok=True)
        media = self._paths.download_media_file(job, track)
        media.write_bytes(b"audio")
        return DownloadResult(
            track_id=track.track_id,
            success=True,
            output_path=str(media),
            error_message=None,
            bytes_downloaded=media.stat().st_size,
        )
