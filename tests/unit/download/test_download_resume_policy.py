from pathlib import Path

from ytpd.domain.download_attempt_mode import DownloadAttemptMode
from ytpd.download.download_resume_policy import DownloadResumePolicy


def test_policy_resumes_when_partial_exists(tmp_path: Path) -> None:
    partial = tmp_path / "track.media.part"
    partial.write_bytes(b"partial")
    mode = DownloadResumePolicy().decide(partial)
    assert mode is DownloadAttemptMode.RESUME


def test_policy_full_when_no_partial(tmp_path: Path) -> None:
    partial = tmp_path / "track.media.part"
    mode = DownloadResumePolicy().decide(partial)
    assert mode is DownloadAttemptMode.FULL


def test_policy_clears_partial_after_failed_resume(tmp_path: Path) -> None:
    partial = tmp_path / "track.media.part"
    partial.write_bytes(b"partial")
    policy = DownloadResumePolicy()
    policy.clear_partial(partial)
    assert partial.exists() is False
    assert policy.decide(partial) is DownloadAttemptMode.FULL
