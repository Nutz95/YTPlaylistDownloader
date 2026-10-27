from dataclasses import dataclass


@dataclass(frozen=True)
class TranscodeProgressSnapshot:
    """Live MP3 encode progress for one track."""

    track_id: str
    status: str
    backend_label: str
    percent: float | None
    message: str
