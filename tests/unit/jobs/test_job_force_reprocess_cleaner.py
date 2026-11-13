from pathlib import Path

import pytest

from ytpd.catalog.memory_output_catalog import MemoryOutputCatalog
from ytpd.domain.catalog_entry import CatalogEntry
from ytpd.domain.job_media_mode import JobMediaMode
from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.job_status import JobStatus
from ytpd.domain.source_kind import SourceKind
from ytpd.domain.track_phase import TrackPhase
from ytpd.domain.track_ref import TrackRef
from ytpd.jobs.invalid_job_error import InvalidJobError
from ytpd.jobs.job_force_reprocess_cleaner import JobForceReprocessCleaner
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths


def _job(paths: TrackArtifactPaths) -> tuple[JobSnapshot, TrackRef]:
    track = TrackRef(
        track_id="vid",
        title="Clip",
        artist="Channel",
        duration_sec=10,
        source_kind=SourceKind.YOUTUBE_VIDEO,
        phase=TrackPhase.DONE,
        youtube_url="https://youtu.be/vid",
        deezer_id=None,
        error_message=None,
    )
    job = JobSnapshot(
        job_id="job-1",
        source_url="https://youtu.be/vid",
        source_kind=SourceKind.YOUTUBE_VIDEO,
        status=JobStatus.QUEUED,
        tracks=[track],
        error_message=None,
        media_mode=JobMediaMode.VIDEO,
        force_reprocess=True,
    )
    return job, track


def test_cleaner_removes_work_destination_and_catalog(tmp_path: Path) -> None:
    paths = TrackArtifactPaths(tmp_path / "work", tmp_path / "out")
    catalog = MemoryOutputCatalog()
    job, track = _job(paths)
    media = paths.download_media_file(job, track)
    marker = paths.download_complete_marker(job, track)
    dest = paths.destination_file(job, track)
    media.parent.mkdir(parents=True)
    dest.parent.mkdir(parents=True)
    media.write_bytes(b"media")
    marker.write_text("ok", encoding="utf-8")
    dest.write_bytes(b"out")
    catalog.upsert(
        CatalogEntry(
            track_id=track.track_id,
            title=track.title,
            artist=track.artist,
            output_path=str(dest),
            youtube_url=track.youtube_url,
            deezer_id=None,
        )
    )

    JobForceReprocessCleaner(paths, catalog).clear(job)

    assert not media.exists()
    assert not marker.exists()
    assert not dest.exists()
    assert catalog.list_entries() == []


def test_cleaner_raises_when_destination_remains(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = TrackArtifactPaths(tmp_path / "work", tmp_path / "out")
    catalog = MemoryOutputCatalog()
    job, track = _job(paths)
    dest = paths.destination_file(job, track)
    dest.parent.mkdir(parents=True)
    dest.write_bytes(b"locked")

    def _fail_unlink(self: Path) -> None:
        raise OSError("locked")

    monkeypatch.setattr(Path, "unlink", _fail_unlink)
    with pytest.raises(InvalidJobError, match="could not delete"):
        JobForceReprocessCleaner(paths, catalog).clear(job)
