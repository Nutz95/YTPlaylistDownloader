from pathlib import Path

import pytest

from tests.fakes.fake_path_unlinker import FakePathUnlinker
from tests.fakes.force_reprocess_job_parts import ForceReprocessJobParts
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
from ytpd.jobs.os_path_unlinker import OsPathUnlinker
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths


def _job_parts() -> ForceReprocessJobParts:
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
    return ForceReprocessJobParts(job=job, track=track)


def test_cleaner_removes_work_destination_and_catalog(tmp_path: Path) -> None:
    paths = TrackArtifactPaths(tmp_path / "work", tmp_path / "out")
    catalog = MemoryOutputCatalog()
    parts = _job_parts()
    media = paths.download_media_file(parts.job, parts.track)
    marker = paths.download_complete_marker(parts.job, parts.track)
    dest = paths.destination_file(parts.job, parts.track)
    media.parent.mkdir(parents=True)
    dest.parent.mkdir(parents=True)
    media.write_bytes(b"media")
    marker.write_text("ok", encoding="utf-8")
    dest.write_bytes(b"out")
    catalog.upsert(
        CatalogEntry(
            track_id=parts.track.track_id,
            title=parts.track.title,
            artist=parts.track.artist,
            output_path=str(dest),
            youtube_url=parts.track.youtube_url,
            deezer_id=None,
        )
    )

    JobForceReprocessCleaner(paths, catalog, OsPathUnlinker()).clear(parts.job)

    assert not media.exists()
    assert not marker.exists()
    assert not dest.exists()
    assert catalog.list_entries() == []


def test_cleaner_raises_when_destination_remains(tmp_path: Path) -> None:
    paths = TrackArtifactPaths(tmp_path / "work", tmp_path / "out")
    catalog = MemoryOutputCatalog()
    parts = _job_parts()
    dest = paths.destination_file(parts.job, parts.track)
    dest.parent.mkdir(parents=True)
    dest.write_bytes(b"locked")
    unlinker = FakePathUnlinker(refuse=[dest])
    with pytest.raises(InvalidJobError, match="could not delete"):
        JobForceReprocessCleaner(paths, catalog, unlinker).clear(parts.job)
