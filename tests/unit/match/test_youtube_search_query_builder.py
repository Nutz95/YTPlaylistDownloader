from ytpd.match.youtube_search_query_builder import YoutubeSearchQueryBuilder


def test_primary_strips_feat_and_colon_spam() -> None:
    builder = YoutubeSearchQueryBuilder()
    query = builder.primary(
        "Ezra Collective",
        "God Gave Me Feet For Dancing (feat. Yazmin Lacey)",
    )
    assert query == "Ezra Collective God Gave Me Feet For Dancing"
    classical = builder.primary(
        "John Alldis Choir",
        (
            "Messiah, HWV 56, Pt. 2 : Handel: Messiah, HWV 56, Pt. 2: "
            "Georg Friederich HAENDEL : Le Messie. Alléluia"
        ),
    )
    assert classical == "John Alldis Choir Messiah, HWV 56, Pt. 2"


def test_fallbacks_fold_accents_and_add_lyrics() -> None:
    builder = YoutubeSearchQueryBuilder()
    fallbacks = builder.fallbacks("Mylène Farmer", "Libertine")
    assert "Mylene Farmer Libertine" in fallbacks
    assert "Mylene Farmer Libertine lyrics" in fallbacks
    assert "Mylene Farmer Libertine audio" in fallbacks


def test_fallbacks_include_generique_and_quoted_aria() -> None:
    builder = YoutubeSearchQueryBuilder()
    cats = builder.fallbacks("B. Rissoll", "Signé Cat's Eyes")
    assert any("generique" in query for query in cats)
    verdi = builder.fallbacks(
        "Gabriele Santini",
        'Verdi : La Traviata : Act 1 "Libiam ne\' lieti calici" [Alfredo, Chorus]',
    )
    assert any("Libiam ne' lieti calici" in query for query in verdi)
