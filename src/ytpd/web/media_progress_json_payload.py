from typing import NotRequired, TypedDict

from ytpd.web.match_candidate_json_payload import MatchCandidateJsonPayload
from ytpd.web.track_phase_name import TrackPhaseName


class MediaProgressJsonPayload(TypedDict):
    """JSON shape for one active media progress row."""

    track_id: str
    title: str
    artist: str
    phase_label: TrackPhaseName
    detail: str
    candidates: NotRequired[list[MatchCandidateJsonPayload]]
