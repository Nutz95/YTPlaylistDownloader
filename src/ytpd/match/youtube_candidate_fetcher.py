from ytpd.domain.match_candidate import MatchCandidate
from ytpd.domain.track_ref import TrackRef
from ytpd.domain.ytdlp_flat_entry import YtdlpFlatEntry
from ytpd.match.static_match_scorer import StaticMatchScorer
from ytpd.match.youtube_search_query_builder import YoutubeSearchQueryBuilder
from ytpd.ports.youtube_search_client import YoutubeSearchClient

_SEARCH_LIMIT = 5


class YoutubeCandidateFetcher:
    """Search YouTube and score hits for one track."""

    def __init__(
        self,
        search_client: YoutubeSearchClient,
        scorer: StaticMatchScorer,
        query_builder: YoutubeSearchQueryBuilder | None = None,
    ) -> None:
        self._search_client = search_client
        self._scorer = scorer
        self._query_builder = query_builder or YoutubeSearchQueryBuilder()

    def fetch(self, track: TrackRef) -> list[MatchCandidate]:
        """Return scored candidates, trying fallback queries when search is empty."""
        queries = self._queries_for(track)
        return self._fetch_queries(track, queries, excluded_urls=set())

    def fetch_retry_excluding(
        self,
        track: TrackRef,
        excluded_urls: set[str],
    ) -> list[MatchCandidate]:
        """Search with retry queries, skipping previously rejected URLs."""
        queries = self._query_builder.retry_queries(track.artist, track.title)
        if len(queries) == 0:
            queries = self._query_builder.fallbacks(track.artist, track.title)
        return self._fetch_queries(track, queries, excluded_urls)

    def _fetch_queries(
        self,
        track: TrackRef,
        queries: list[str],
        excluded_urls: set[str],
    ) -> list[MatchCandidate]:
        if len(queries) == 0:
            return []
        for query in queries:
            entries = self._search_client.search(query, _SEARCH_LIMIT)
            candidates = self._score_entries(track, entries, excluded_urls)
            if len(candidates) > 0:
                return candidates
        return []

    def _queries_for(self, track: TrackRef) -> list[str]:
        primary = self._query_builder.primary(track.artist, track.title)
        if primary == "":
            return []
        return [primary, *self._query_builder.fallbacks(track.artist, track.title)]

    def _score_entries(
        self,
        track: TrackRef,
        entries: list[YtdlpFlatEntry],
        excluded_urls: set[str],
    ) -> list[MatchCandidate]:
        candidates: list[MatchCandidate] = []
        for entry in entries:
            if entry.webpage_url in excluded_urls:
                continue
            candidates.append(
                MatchCandidate(
                    youtube_url=entry.webpage_url,
                    title=entry.title,
                    channel=entry.uploader,
                    duration_sec=entry.duration_sec,
                    score=self._scorer.score(track, entry),
                )
            )
        return candidates
