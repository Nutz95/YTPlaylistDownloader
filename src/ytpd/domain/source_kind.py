from enum import Enum


class SourceKind(Enum):
    """Origin of a track or playlist URL."""

    DEEZER_PLAYLIST = "deezer_playlist"
    YOUTUBE_PLAYLIST = "youtube_playlist"
    YOUTUBE_VIDEO = "youtube_video"
    UNKNOWN = "unknown"
