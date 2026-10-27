from datetime import datetime, timezone
from pathlib import Path

from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.track_ref import TrackRef
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths


class JobFailureLog:
    """Append human-readable failure lines under the job work directory."""

    def __init__(self, paths: TrackArtifactPaths) -> None:
        self._paths = paths

    def append(self, job: JobSnapshot, track: TrackRef, message: str) -> Path:
        """Append one failure line and return the log file path."""
        work = self._paths.job_work_dir(job)
        work.mkdir(parents=True, exist_ok=True)
        log_path = work / "failures.log"
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        line = (
            f"{stamp}\t{track.phase.value}\t{track.track_id}\t"
            f"{track.artist} — {track.title}\t{message}\n"
        )
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(line)
        return log_path

    def path_for(self, job: JobSnapshot) -> Path:
        """Return the failures log path for ``job`` (may not exist yet)."""
        return self._paths.job_work_dir(job) / "failures.log"
