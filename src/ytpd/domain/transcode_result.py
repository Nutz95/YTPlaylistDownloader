from dataclasses import dataclass

from ytpd.domain.transcode_backend_kind import TranscodeBackendKind


@dataclass(frozen=True)
class TranscodeResult:
    """Outcome of transcoding one downloaded track to MP3."""

    track_id: str
    success: bool
    output_path: str | None
    backend: TranscodeBackendKind | None
    error_message: str | None
