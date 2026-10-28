from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.job_status import JobStatus
from ytpd.domain.source_kind import SourceKind
from ytpd.jobs.job_queue_next_picker import JobQueueNextPicker


def _job(job_id: str, status: JobStatus) -> JobSnapshot:
    return JobSnapshot(
        job_id=job_id,
        source_url=f"https://example.test/{job_id}",
        source_kind=SourceKind.UNKNOWN,
        status=status,
        tracks=[],
        error_message=None,
    )


def test_prefers_oldest_queued_over_interrupted() -> None:
    picker = JobQueueNextPicker()
    jobs = [
        _job("interrupted", JobStatus.INTERRUPTED),
        _job("queued-a", JobStatus.QUEUED),
        _job("queued-b", JobStatus.QUEUED),
    ]
    assert picker.pick(jobs) == "queued-a"


def test_falls_back_to_interrupted_when_no_queued() -> None:
    picker = JobQueueNextPicker()
    jobs = [
        _job("done", JobStatus.COMPLETED),
        _job("interrupted", JobStatus.INTERRUPTED),
        _job("failed", JobStatus.FAILED),
    ]
    assert picker.pick(jobs) == "interrupted"


def test_returns_none_when_nothing_auto_startable() -> None:
    picker = JobQueueNextPicker()
    jobs = [
        _job("done", JobStatus.COMPLETED),
        _job("failed", JobStatus.FAILED),
        _job("cancelled", JobStatus.CANCELLED),
    ]
    assert picker.pick(jobs) is None
