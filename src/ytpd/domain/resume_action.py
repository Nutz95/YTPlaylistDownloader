from enum import Enum


class ResumeAction(Enum):
    """Next pipeline step required to continue one track or job."""

    RESOLVE_PLAYLIST = "resolve_playlist"
    MATCH = "match"
    DOWNLOAD = "download"
    TRANSCODE = "transcode"
    NONE = "none"
