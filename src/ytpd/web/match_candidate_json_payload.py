from typing import TypedDict


class MatchCandidateJsonPayload(TypedDict):
    """JSON shape for one persisted YouTube match candidate."""

    youtube_url: str
    title: str
    channel: str
    duration_sec: int | None
