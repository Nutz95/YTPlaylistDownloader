from ytpd.domain.global_progress import GlobalProgress
from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.job_status import JobStatus
from ytpd.domain.media_progress import MediaProgress
from ytpd.domain.pipeline_stage import PipelineStage
from ytpd.domain.progress_snapshot import ProgressSnapshot
from ytpd.domain.stage_progress_counts import StageProgressCounts
from ytpd.domain.track_phase import TrackPhase
from ytpd.domain.track_phase_sets import (
    ACTIVE_TRACK_PHASES,
    DONE_TRACK_PHASES,
    DOWNLOAD_DONE_TRACK_PHASES,
    FAILED_TRACK_PHASES,
    MATCH_DONE_TRACK_PHASES,
    MEDIA_DONE_TRACK_PHASES,
    TRANSCODE_DONE_TRACK_PHASES,
)
from ytpd.domain.track_phase_weights import TRACK_PHASE_WEIGHTS
from ytpd.domain.track_ref import TrackRef
from ytpd.download.download_progress_detail_formatter import (
    DownloadProgressDetailFormatter,
)
from ytpd.ports.download_progress_store import DownloadProgressStore
from ytpd.ports.transcode_progress_store import TranscodeProgressStore
from ytpd.transcode.transcode_progress_detail_formatter import (
    TranscodeProgressDetailFormatter,
)

_ACTIVE_MEDIA_LIMIT = 12
_FAILED_MEDIA_LIMIT = 20


class ProgressCalculator:
    """Build a progress snapshot from a job snapshot."""

    def __init__(
        self,
        download_progress_store: DownloadProgressStore,
        transcode_progress_store: TranscodeProgressStore | None = None,
        transcode_slot_count: int = 0,
    ) -> None:
        self._download_progress_store = download_progress_store
        self._transcode_progress_store = transcode_progress_store
        self._transcode_slot_count = max(0, transcode_slot_count)
        self._download_formatter = DownloadProgressDetailFormatter()
        self._transcode_formatter = TranscodeProgressDetailFormatter()

    def from_job(self, job: JobSnapshot) -> ProgressSnapshot:
        """Compute global and active-media progress for ``job``."""
        total = len(job.tracks)
        completed = sum(1 for track in job.tracks if track.phase in DONE_TRACK_PHASES)
        failed = sum(1 for track in job.tracks if track.phase in FAILED_TRACK_PHASES)
        weight_sum = sum(
            TRACK_PHASE_WEIGHTS.get(track.phase, 0.0) for track in job.tracks
        )
        percent = 0.0 if total == 0 else (weight_sum / total) * 100.0
        stage = job.pipeline_stage.value if job.pipeline_stage is not None else "idle"
        counts = self._stage_counts(job, completed, total)
        label = self._label(job, completed, total, percent, stage, counts, failed)
        active = [
            self._media(job, track)
            for track in job.tracks
            if track.phase in ACTIVE_TRACK_PHASES
        ][:_ACTIVE_MEDIA_LIMIT]
        failed_media = [
            self._media(job, track)
            for track in job.tracks
            if track.phase in FAILED_TRACK_PHASES
        ][:_FAILED_MEDIA_LIMIT]
        return ProgressSnapshot(
            job_id=job.job_id,
            job_status=job.status,
            global_progress=GlobalProgress(
                percent=percent,
                completed_tracks=completed,
                total_tracks=total,
                label=label,
                stage=stage,
                stage_done=counts.done,
                stage_total=counts.total,
            ),
            active_media=active,
            failed_media=failed_media,
        )

    def _stage_counts(
        self,
        job: JobSnapshot,
        completed: int,
        total: int,
    ) -> StageProgressCounts:
        stage = job.pipeline_stage
        tracks = job.tracks
        if stage is PipelineStage.MATCH:
            done = sum(1 for track in tracks if track.phase in MATCH_DONE_TRACK_PHASES)
            return StageProgressCounts(done=done, total=total)
        if stage is PipelineStage.DOWNLOAD:
            eligible = [
                track
                for track in tracks
                if track.phase not in {TrackPhase.SKIPPED, TrackPhase.MATCH_FAILED}
            ]
            done = sum(
                1 for track in eligible if track.phase in DOWNLOAD_DONE_TRACK_PHASES
            )
            return StageProgressCounts(done=done, total=len(eligible))
        if stage is PipelineStage.TRANSCODE:
            eligible = [
                track
                for track in tracks
                if track.phase
                in {
                    TrackPhase.DOWNLOADED,
                    TrackPhase.TRANSCODING,
                    TrackPhase.DONE,
                    TrackPhase.SKIPPED,
                }
            ]
            done = sum(
                1 for track in eligible if track.phase in TRANSCODE_DONE_TRACK_PHASES
            )
            return StageProgressCounts(done=done, total=len(eligible))
        if stage is PipelineStage.MEDIA:
            eligible = [
                track
                for track in tracks
                if track.phase not in {TrackPhase.SKIPPED, TrackPhase.MATCH_FAILED}
            ]
            done = sum(
                1 for track in eligible if track.phase in MEDIA_DONE_TRACK_PHASES
            )
            return StageProgressCounts(done=done, total=len(eligible))
        if stage is PipelineStage.RESOLVE:
            return StageProgressCounts(done=1 if total > 0 else 0, total=1)
        return StageProgressCounts(done=completed, total=total)

    def _label(
        self,
        job: JobSnapshot,
        completed: int,
        total: int,
        percent: float,
        stage: str,
        counts: StageProgressCounts,
        failed: int,
    ) -> str:
        status = job.status.value
        focus = self._focus_track(job)
        focus_text = ""
        if focus is not None:
            focus_text = f" · {focus.artist} — {focus.title}"
        fail_text = f" · fails {failed}" if failed > 0 else ""
        slots_text = self._slots_text(job, stage)
        if stage == "idle":
            return (
                f"{status} · done {completed}/{total} ({percent:.1f}%)"
                f"{fail_text}{focus_text}"
            )
        return (
            f"{status} · {stage} {counts.done}/{counts.total}"
            f" · overall {percent:.1f}%{slots_text}{fail_text}{focus_text}"
        )

    def _slots_text(self, job: JobSnapshot, stage: str) -> str:
        if stage not in {"download", "transcode", "media"}:
            return ""
        if self._transcode_slot_count <= 0:
            return ""
        encoding = sum(1 for track in job.tracks if track.phase is TrackPhase.TRANSCODING)
        if encoding == 0 and stage == "download":
            return ""
        return f" · CPU×{self._transcode_slot_count} ({encoding} encoding)"

    def _focus_track(self, job: JobSnapshot) -> TrackRef | None:
        for track in job.tracks:
            if track.phase in ACTIVE_TRACK_PHASES:
                return track
        return None

    def _media(self, job: JobSnapshot, track: TrackRef) -> MediaProgress:
        return MediaProgress(
            track_id=track.track_id,
            title=track.title,
            artist=track.artist,
            phase=track.phase,
            detail=self._detail_for(job, track),
            candidates=list(track.match_candidates),
        )

    def _detail_for(self, job: JobSnapshot, track: TrackRef) -> str:
        if track.phase in FAILED_TRACK_PHASES:
            return track.error_message or "failed"
        if track.phase is TrackPhase.DOWNLOADING:
            return self._download_detail(track)
        if track.phase is TrackPhase.MATCHING:
            return "matching…"
        if track.phase is TrackPhase.TRANSCODING:
            return self._transcode_detail(job, track)
        return track.error_message or "in progress"

    def _download_detail(self, track: TrackRef) -> str:
        media_key = (
            track.parent_video_id.strip()
            if track.parent_video_id is not None and track.parent_video_id.strip() != ""
            else track.track_id
        )
        snapshot = self._download_progress_store.get_snapshot(media_key)
        if snapshot is None:
            return "audio download… (no live % yet)"
        return self._download_formatter.format(snapshot)

    def _transcode_detail(self, job: JobSnapshot, track: TrackRef) -> str:
        if job.status is not JobStatus.RUNNING:
            return "pipeline stopped — Resume / Run to continue"
        if self._transcode_progress_store is None:
            return "CPU · encoding… (MP3/lame, no GPU)"
        snapshot = self._transcode_progress_store.get_snapshot(track.track_id)
        if snapshot is None:
            return "CPU · waiting for encode slot…"
        return self._transcode_formatter.format(snapshot)
