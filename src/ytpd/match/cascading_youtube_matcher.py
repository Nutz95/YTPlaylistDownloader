from dataclasses import replace

from ytpd.domain.match_candidate import MatchCandidate
from ytpd.domain.match_result import MatchResult
from ytpd.domain.track_ref import TrackRef
from ytpd.match.static_match_decider import StaticMatchDecider
from ytpd.match.youtube_candidate_fetcher import YoutubeCandidateFetcher
from ytpd.ports.lm_studio_client import LmStudioClient
from ytpd.ports.resource_gate import ResourceGate
from ytpd.resolve.ytdlp_probe_error import YtdlpProbeError


class CascadingYoutubeMatcher:
    """Search, static decide, then LM choose + verify with one rejection retry."""

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
                candidates=[],
            )
        try:
            candidates = self._fetcher.fetch(track)
        except YtdlpProbeError as error:
            return MatchResult(
                track_id=track.track_id,
                matched=False,
                candidate=None,
                error_message=str(error),
                candidates=[],
            )
        static_result = self._decider.decide(track.track_id, candidates)
        if static_result.matched:
            return self._with_candidates(static_result, candidates)
        if len(candidates) == 0:
            return self._with_candidates(static_result, candidates)
        first = self._llm_pass(track, candidates, rejection_context=None)
        if first.matched:
            return self._with_candidates(first, candidates)
        return self._retry_after_rejection(track, candidates, first)

    def _retry_after_rejection(
        self,
        track: TrackRef,
        first_candidates: list[MatchCandidate],
        first_result: MatchResult,
    ) -> MatchResult:
        excluded = {candidate.youtube_url for candidate in first_candidates}
        rejection = first_result.error_message or "previous candidate rejected"
        if first_result.candidate is not None:
            excluded.add(first_result.candidate.youtube_url)
            rejection = (
                f"{first_result.candidate.title} "
                f"({first_result.candidate.youtube_url}): {rejection}"
            )
        try:
            retry_candidates = self._fetcher.fetch_retry_excluding(track, excluded)
        except YtdlpProbeError:
            return self._with_candidates(first_result, first_candidates)
        merged = self._merge_unique(first_candidates, retry_candidates)
        if len(retry_candidates) == 0:
            return self._with_candidates(first_result, merged)
        retry_result = self._llm_pass(
            track,
            retry_candidates,
            rejection_context=rejection,
        )
        if retry_result.matched:
            return self._with_candidates(retry_result, merged)
        return MatchResult(
            track_id=track.track_id,
            matched=False,
            candidate=retry_result.candidate or first_result.candidate,
            error_message=retry_result.error_message or first_result.error_message,
            candidates=merged,
        )

    def _llm_pass(
        self,
        track: TrackRef,
        candidates: list[MatchCandidate],
        rejection_context: str | None,
    ) -> MatchResult:
        self._resource_gate.acquire_llm()
        try:
            choice = self._lm_client.choose_match(
                track,
                candidates,
                rejection_context=rejection_context,
            )
            if choice.candidate_index is None:
                best = sorted(
                    candidates,
                    key=lambda item: item.score.value,
                    reverse=True,
                )[0]
                return MatchResult(
                    track_id=track.track_id,
                    matched=False,
                    candidate=best,
                    error_message=choice.error_message,
                    candidates=candidates,
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
                candidates=candidates,
            )
        return MatchResult(
            track_id=track.track_id,
            matched=True,
            candidate=selected,
            error_message=None,
            candidates=candidates,
        )

    def _with_candidates(
        self,
        result: MatchResult,
        candidates: list[MatchCandidate],
    ) -> MatchResult:
        return replace(result, candidates=candidates)

    def _merge_unique(
        self,
        first: list[MatchCandidate],
        second: list[MatchCandidate],
    ) -> list[MatchCandidate]:
        merged: list[MatchCandidate] = []
        seen: set[str] = set()
        for candidate in [*first, *second]:
            if candidate.youtube_url in seen:
                continue
            seen.add(candidate.youtube_url)
            merged.append(candidate)
        return merged
