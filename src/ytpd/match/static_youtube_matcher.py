from ytpd.domain.match_candidate import MatchCandidate
from ytpd.domain.match_result import MatchResult
from ytpd.domain.track_ref import TrackRef
from ytpd.match.static_match_scorer import StaticMatchScorer
from ytpd.ports.youtube_search_client import YoutubeSearchClient
from ytpd.resolve.ytdlp_probe_error import YtdlpProbeError

_MIN_SCORE = 55.0
_SEARCH_LIMIT = 5


class StaticYoutubeMatcher:
    """Match Deezer tracks via yt-dlp search scoring (no LLM)."""

    def __init__(
        self,
        search_client: YoutubeSearchClient,
        scorer: StaticMatchScorer,
    ) -> None:
        self._search_client = search_client
        self._scorer = scorer

    def match(self, track: TrackRef) -> MatchResult:
        """Search YouTube and return the best candidate above the score floor."""
        query = f"{track.artist} {track.title}".strip()
        if query == "":
            return MatchResult(
                track_id=track.track_id,
                matched=False,
                candidate=None,
                error_message="empty match query",
            )
        try:
            entries = self._search_client.search(query, _SEARCH_LIMIT)
        except YtdlpProbeError as error:
            return MatchResult(
                track_id=track.track_id,
                matched=False,
                candidate=None,
                error_message=str(error),
            )
        if len(entries) == 0:
            return MatchResult(
                track_id=track.track_id,
                matched=False,
                candidate=None,
                error_message="no youtube search hits",
            )
        ranked = sorted(
            (
                MatchCandidate(
                    youtube_url=entry.webpage_url,
                    title=entry.title,
                    channel=entry.uploader,
                    duration_sec=entry.duration_sec,
                    score=self._scorer.score(track, entry),
                )
                for entry in entries
            ),
            key=lambda item: item.score.value,
            reverse=True,
        )
        best = ranked[0]
        if best.score.value < _MIN_SCORE:
            return MatchResult(
                track_id=track.track_id,
                matched=False,
                candidate=best,
                error_message="best candidate below score floor",
            )
        return MatchResult(
            track_id=track.track_id,
            matched=True,
            candidate=best,
            error_message=None,
        )
