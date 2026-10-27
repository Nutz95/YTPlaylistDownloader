from typing import NotRequired, TypedDict

from ytpd.web.match_candidate_json_payload import MatchCandidateJsonPayload
from ytpd.web.source_kind_name import SourceKindName
from ytpd.web.track_phase_name import TrackPhaseName


class TrackJsonPayload(TypedDict):
    """JSON shape for one track in job API responses."""

    track_id: str
    title: str
    artist: str
    duration_sec: int | None
    source_kind: SourceKindName
    phase: TrackPhaseName
    youtube_url: str | None
    deezer_id: str | None
    error_message: str | None
    chapter_start_sec: NotRequired[float | None]
    chapter_end_sec: NotRequired[float | None]
    parent_video_id: NotRequired[str | None]
    chapter_index: NotRequired[int | None]
    match_candidates: NotRequired[list[MatchCandidateJsonPayload]]
