from enum import Enum


class TranscodeBackendKind(Enum):
    """Available media decode/transcode backends."""

    NVIDIA = "nvidia"
    ARC = "arc"
    CPU = "cpu"
