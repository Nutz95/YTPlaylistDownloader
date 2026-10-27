from ytpd.domain.match_candidate import MatchCandidate
from ytpd.domain.match_score import MatchScore
from ytpd.match.persisted_match_candidate_mapper import PersistedMatchCandidateMapper


def test_mapper_keeps_top_scored_without_score_field() -> None:
    mapped = PersistedMatchCandidateMapper().from_scored(
        [
            MatchCandidate("https://youtu.be/a", "A", "Ch", 10, MatchScore(10.0)),
            MatchCandidate("https://youtu.be/b", "B", "Ch", 20, MatchScore(90.0)),
            MatchCandidate("https://youtu.be/c", "C", "Ch", 30, MatchScore(50.0)),
        ]
    )
    assert [item.youtube_url for item in mapped] == [
        "https://youtu.be/b",
        "https://youtu.be/c",
        "https://youtu.be/a",
    ]
    assert mapped[0].title == "B"
    assert mapped[0].duration_sec == 20
