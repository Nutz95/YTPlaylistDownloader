from ytpd.domain.match_candidate import MatchCandidate
from ytpd.domain.track_ref import TrackRef
from ytpd.match.static_match_scorer import StaticMatchScorer
from ytpd.ports.youtube_search_client import YoutubeSearchClient

_SEARCH_LIMIT = 5


class YoutubeCandidateFetcher:
    """Search YouTube and score hits for one track."""

    def __init__(
        self,
        search_client: YoutubeSearchClient,
        scorer: StaticMatchScorer,
    ) -> None:
        self._search_client = search_client
        self._scorer = scorer

    def fetch(self, track: TrackRef) -> list[MatchCandidate]:
        """Return scored candidates, or raise ``YtdlpProbeError`` on probe failure."""
        query = f"{track.artist} {track.title}".strip()
        if query == "":
            return []
        entries = self._search_client.search(query, _SEARCH_LIMIT)
        return [
            MatchCandidate(
                youtube_url=entry.webpage_url,
                title=entry.title,
                channel=entry.uploader,
                duration_sec=entry.duration_sec,
                score=self._scorer.score(track, entry),
            )
            for entry in entries
        ]
