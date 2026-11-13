from enum import Enum


class JobMediaMode(Enum):
    """Output mode for a job: audio MP3 pipeline or best-quality video."""

    AUDIO = "audio"
    VIDEO = "video"
