from ytpd.domain.source_kind import SourceKind
from ytpd.domain.track_phase import TrackPhase
from ytpd.domain.track_ref import TrackRef
from ytpd.jobs.video_chapter_collapser import VideoChapterCollapser


def _chapter(index: int, title: str) -> TrackRef:
    return TrackRef(
        track_id=f"vid__ch{index:02d}",
        title=title,
        artist="Uploader",
        duration_sec=30,
        source_kind=SourceKind.YOUTUBE_VIDEO,
        phase=TrackPhase.MATCHED,
        youtube_url="https://youtu.be/vid",
        deezer_id=None,
        error_message=None,
        chapter_start_sec=float(index * 30),
        chapter_end_sec=float((index + 1) * 30),
        parent_video_id="vid",
        chapter_index=index,
    )


def test_collapse_keeps_one_full_video_per_parent() -> None:
    tracks = [_chapter(0, "Intro"), _chapter(1, "Verse")]
    collapsed = VideoChapterCollapser().collapse(tracks, "Full Title")
    assert len(collapsed) == 1
    track = collapsed[0]
    assert track.track_id == "vid"
    assert track.title == "Full Title"
    assert track.duration_sec == 60
    assert track.chapter_start_sec is None
    assert track.chapter_end_sec is None
    assert track.parent_video_id is None
    assert track.chapter_index is None
    assert track.youtube_url == "https://youtu.be/vid"


def test_collapse_leaves_plain_tracks_unchanged() -> None:
    plain = TrackRef(
        track_id="plain",
        title="Song",
        artist="Artist",
        duration_sec=10,
        source_kind=SourceKind.YOUTUBE_VIDEO,
        phase=TrackPhase.MATCHED,
        youtube_url="https://youtu.be/plain",
        deezer_id=None,
        error_message=None,
    )
    collapsed = VideoChapterCollapser().collapse([plain], None)
    assert collapsed == [plain]
