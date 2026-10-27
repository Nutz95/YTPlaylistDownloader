from dataclasses import dataclass


@dataclass(frozen=True)
class PersistedMatchCandidate:
    """YouTube candidate kept on a failed track for manual UI selection."""

    youtube_url: str
    title: str
    channel: str
    duration_sec: int | None
