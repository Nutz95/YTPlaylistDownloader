from enum import Enum


class PipelineStage(Enum):
    """Coarse pipeline stage shown in job progress UI."""

    RESOLVE = "resolve"
    MATCH = "match"
    DOWNLOAD = "download"
    TRANSCODE = "transcode"
    MEDIA = "media"
