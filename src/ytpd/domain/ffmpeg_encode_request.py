from dataclasses import dataclass
from pathlib import Path

from ytpd.domain.transcode_backend_kind import TranscodeBackendKind


@dataclass(frozen=True)
class FfmpegEncodeRequest:
    """Parameters for one ffmpeg MP3 encode, optionally chapter-sliced."""

    track_id: str
    source: Path
    destination: Path
    backend: TranscodeBackendKind
    chapter_start_sec: float | None
    chapter_duration_sec: float | None
    metadata_title: str | None
    metadata_artist: str | None
    expected_duration_sec: float | None
