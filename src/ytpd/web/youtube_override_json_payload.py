from typing import TypedDict


class YoutubeOverrideJsonPayload(TypedDict):
    """JSON body for a manual YouTube URL override on one track."""

    youtube_url: str
