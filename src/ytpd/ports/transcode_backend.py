from typing import Protocol

from ytpd.domain.transcode_backend_kind import TranscodeBackendKind
from ytpd.domain.transcode_result import TranscodeResult
from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.track_ref import TrackRef


class TranscodeBackend(Protocol):
    """Transcode one downloaded track into a destination MP3."""

    def kind(self) -> TranscodeBackendKind:
        """Return the backend identity."""

    def transcode(self, job: JobSnapshot, track: TrackRef) -> TranscodeResult:
        """Produce an MP3 for ``track`` using this backend."""
