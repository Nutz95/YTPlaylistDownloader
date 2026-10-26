from dataclasses import dataclass


@dataclass(frozen=True)
class TrackArtifactFlags:
    """Filesystem presence flags used by the resume decision table."""

    download_complete: bool
    mp3_present: bool
