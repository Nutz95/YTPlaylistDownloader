from ytpd.domain.match_score import MatchScore
from ytpd.domain.track_ref import TrackRef
from ytpd.domain.ytdlp_flat_entry import YtdlpFlatEntry


class StaticMatchScorer:
    """Score a YouTube search hit against a Deezer track with simple heuristics."""

    def score(self, track: TrackRef, entry: YtdlpFlatEntry) -> MatchScore:
        """Return a 0..100 score based on title/artist/duration overlap."""
        haystack = f"{entry.title} {entry.uploader}".casefold()
        title_hit = track.title.casefold() in haystack
        artist_hit = track.artist.casefold() in haystack if track.artist else False
        value = 0.0
        if title_hit:
            value += 55.0
        if artist_hit:
            value += 35.0
        if (
            track.duration_sec is not None
            and entry.duration_sec is not None
            and abs(track.duration_sec - entry.duration_sec) <= 8
        ):
            value += 10.0
        return MatchScore(value=value)
