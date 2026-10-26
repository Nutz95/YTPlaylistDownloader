from enum import Enum


class DownloadAttemptMode(Enum):
    """How the next download attempt should treat existing partial files."""

    RESUME = "resume"
    FULL = "full"
