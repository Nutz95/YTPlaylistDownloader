from enum import Enum


class TrackPhase(Enum):
    """Lifecycle phase of one track inside a job."""

    PENDING = "pending"
    RESOLVED = "resolved"
    MATCHING = "matching"
    MATCHED = "matched"
    MATCH_FAILED = "match_failed"
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    TRANSCODING = "transcoding"
    DONE = "done"
    SKIPPED = "skipped"
    ERROR = "error"
