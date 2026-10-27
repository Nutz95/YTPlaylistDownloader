from ytpd.domain.match_result import MatchResult
from ytpd.domain.track_ref import TrackRef
from ytpd.match.static_match_decider import StaticMatchDecider
from ytpd.match.youtube_candidate_fetcher import YoutubeCandidateFetcher
from ytpd.ports.lm_studio_client import LmStudioClient
from ytpd.ports.resource_gate import ResourceGate
from ytpd.resolve.ytdlp_probe_error import YtdlpProbeError


class CascadingYoutubeMatcher:
    """Search once, try static decide, then LM choose + verify on the same candidates."""

    def __init__(
        self,
        fetcher: YoutubeCandidateFetcher,
        decider: StaticMatchDecider,
        lm_client: LmStudioClient,
        resource_gate: ResourceGate,
    ) -> None:
        self._fetcher = fetcher
        self._decider = decider
        self._lm_client = lm_client
        self._resource_gate = resource_gate

    def match(self, track: TrackRef) -> MatchResult:
        """Match ``track`` with one search and optional verified LLM fallback."""
        query = f"{track.artist} {track.title}".strip()
        if query == "":
            return MatchResult(
                track_id=track.track_id,
                matched=False,
                candidate=None,
                error_message="empty match query",
            )
        try:
            candidates = self._fetcher.fetch(track)
        except YtdlpProbeError as error:
            return MatchResult(
                track_id=track.track_id,
                matched=False,
                candidate=None,
                error_message=str(error),
            )
        static_result = self._decider.decide(track.track_id, candidates)
        if static_result.matched:
            return static_result
        if len(candidates) == 0:
            return static_result
        self._resource_gate.acquire_llm()
        try:
            choice = self._lm_client.choose_match(track, candidates)
            if choice.candidate_index is None:
                return MatchResult(
                    track_id=track.track_id,
                    matched=False,
                    candidate=static_result.candidate,
                    error_message=choice.error_message,
                )
            selected = candidates[choice.candidate_index]
            verified = self._lm_client.verify_match(track, selected)
        finally:
            self._resource_gate.release_llm()
        if verified.candidate_index is None:
            return MatchResult(
                track_id=track.track_id,
                matched=False,
                candidate=selected,
                error_message=verified.error_message or "LLM: match rejeté",
            )
        return MatchResult(
            track_id=track.track_id,
            matched=True,
            candidate=selected,
            error_message=None,
        )
